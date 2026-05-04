#!/usr/bin/env python3
"""Batch entity rename tool for Home Assistant.

Modifies the local entity registry file and pushes it to HA via SSH.

Usage:
    python tools/rename_entities.py           # dry run (preview only)
    python tools/rename_entities.py --apply   # apply renames and restart HA
"""

import json
import os
import subprocess
import sys
from pathlib import Path


REGISTRY_LOCAL = Path("config/.storage/core.entity_registry")
REGISTRY_REMOTE = "/config/.storage/core.entity_registry"

# ---------------------------------------------------------------------------
# Explicit rename map
# ---------------------------------------------------------------------------
RENAME_MAP = {
    # --- ADU: Cielo climate ---
    "climate.garage":      "climate.adu_garage_cielo",
    "climate.bathroom":    "climate.adu_bathroom_cielo",
    "climate.bedroom":     "climate.adu_bedroom_cielo",
    "climate.living_room": "climate.adu_living_room_cielo",

    # --- ADU: Cielo binary sensors ---
    "binary_sensor.garage_status":      "binary_sensor.adu_garage_cielo_status",
    "binary_sensor.bathroom_status":    "binary_sensor.adu_bathroom_cielo_status",
    "binary_sensor.bedroom_status":     "binary_sensor.adu_bedroom_cielo_status",
    "binary_sensor.living_room_status": "binary_sensor.adu_living_room_cielo_status",

    # --- ADU: Cielo sensors ---
    "sensor.garage_temperature":           "sensor.adu_garage_cielo_temperature",
    "sensor.garage_humidity":              "sensor.adu_garage_cielo_humidity",
    "sensor.garage_target_temperature":    "sensor.adu_garage_cielo_target_temperature",
    "sensor.bathroom_temperature":         "sensor.adu_bathroom_cielo_temperature",
    "sensor.bathroom_humidity":            "sensor.adu_bathroom_cielo_humidity",
    "sensor.bathroom_target_temperature":  "sensor.adu_bathroom_cielo_target_temperature",
    "sensor.bedroom_temperature":          "sensor.adu_bedroom_cielo_temperature",
    "sensor.bedroom_humidity":             "sensor.adu_bedroom_cielo_humidity",
    "sensor.bedroom_target_temperature":   "sensor.adu_bedroom_cielo_target_temperature",
    "sensor.living_room_temperature":          "sensor.adu_living_room_cielo_temperature",
    "sensor.living_room_humidity":             "sensor.adu_living_room_cielo_humidity",
    "sensor.living_room_target_temperature":   "sensor.adu_living_room_cielo_target_temperature",

    # --- ADU: Cielo numbers ---
    "number.garage_target_temperature":         "number.adu_garage_cielo_target_temperature",
    "number.garage_back_light_brightness":      "number.adu_garage_cielo_back_light_brightness",
    "number.garage_temperature_offset":         "number.adu_garage_cielo_temperature_offset",
    "number.bathroom_target_temperature":       "number.adu_bathroom_cielo_target_temperature",
    "number.bathroom_back_light_brightness":    "number.adu_bathroom_cielo_back_light_brightness",
    "number.bathroom_temperature_offset":       "number.adu_bathroom_cielo_temperature_offset",
    "number.bedroom_target_temperature":        "number.adu_bedroom_cielo_target_temperature",
    "number.bedroom_back_light_brightness":     "number.adu_bedroom_cielo_back_light_brightness",
    "number.bedroom_temperature_offset":        "number.adu_bedroom_cielo_temperature_offset",
    "number.living_room_target_temperature":    "number.adu_living_room_cielo_target_temperature",
    "number.living_room_back_light_brightness": "number.adu_living_room_cielo_back_light_brightness",
    "number.living_room_temperature_offset":    "number.adu_living_room_cielo_temperature_offset",

    # --- ADU: Cielo selects ---
    "select.garage_fan":       "select.adu_garage_cielo_fan",
    "select.garage_hvac":      "select.adu_garage_cielo_hvac",
    "select.garage_preset":    "select.adu_garage_cielo_preset",
    "select.garage_swing":     "select.adu_garage_cielo_swing",
    "select.bathroom_fan":     "select.adu_bathroom_cielo_fan",
    "select.bathroom_hvac":    "select.adu_bathroom_cielo_hvac",
    "select.bathroom_preset":  "select.adu_bathroom_cielo_preset",
    "select.bathroom_swing":   "select.adu_bathroom_cielo_swing",
    "select.bedroom_fan":      "select.adu_bedroom_cielo_fan",
    "select.bedroom_hvac":     "select.adu_bedroom_cielo_hvac",
    "select.bedroom_preset":   "select.adu_bedroom_cielo_preset",
    "select.bedroom_swing":    "select.adu_bedroom_cielo_swing",
    "select.living_room_fan":    "select.adu_living_room_cielo_fan",
    "select.living_room_hvac":   "select.adu_living_room_cielo_hvac",
    "select.living_room_preset": "select.adu_living_room_cielo_preset",
    "select.living_room_swing":  "select.adu_living_room_cielo_swing",

    # --- ADU: Cielo switches ---
    "switch.garage_power":      "switch.adu_garage_cielo_power",
    "switch.garage_back_light": "switch.adu_garage_cielo_back_light",

    # --- Home: Ecobee thermostats ---
    "climate.main_floor": "climate.home_main_floor_ecobee",
    "climate.downstairs": "climate.home_downstairs_ecobee",
    "climate.upstairs":   "climate.home_upstairs_ecobee",

    # --- Home: Ecobee binary sensors ---
    "binary_sensor.bedroom_motion":       "binary_sensor.home_office_ecobee_motion",
    "binary_sensor.bedroom_motion_2":     "binary_sensor.home_zack_bedroom_ecobee_motion",
    "binary_sensor.bedroom_motion_3":     "binary_sensor.home_austin_bedroom_ecobee_motion",
    "binary_sensor.bedroom_occupancy":    "binary_sensor.home_office_ecobee_occupancy",
    "binary_sensor.bedroom_occupancy_2":  "binary_sensor.home_zack_bedroom_ecobee_occupancy",
    "binary_sensor.bedroom_occupancy_3":  "binary_sensor.home_austin_bedroom_ecobee_occupancy",
    "binary_sensor.downstairs_motion":    "binary_sensor.home_downstairs_ecobee_motion",
    "binary_sensor.downstairs_occupancy": "binary_sensor.home_downstairs_ecobee_occupancy",
    "binary_sensor.kitchen_motion":       "binary_sensor.home_kitchen_ecobee_motion",
    "binary_sensor.kitchen_occupancy":    "binary_sensor.home_kitchen_ecobee_occupancy",
    "binary_sensor.living_room_motion":       "binary_sensor.home_living_room_ecobee_motion",
    "binary_sensor.living_room_occupancy":    "binary_sensor.home_living_room_ecobee_occupancy",
    "binary_sensor.main_floor_motion":    "binary_sensor.home_main_floor_ecobee_motion",
    "binary_sensor.main_floor_occupancy": "binary_sensor.home_main_floor_ecobee_occupancy",
    "binary_sensor.tv_room_motion":       "binary_sensor.home_living_room_2_ecobee_motion",
    "binary_sensor.tv_room_occupancy":    "binary_sensor.home_living_room_2_ecobee_occupancy",
    "binary_sensor.upstairs_motion":      "binary_sensor.home_upstairs_ecobee_motion",
    "binary_sensor.upstairs_occupancy":   "binary_sensor.home_upstairs_ecobee_occupancy",

    # --- Home: Ecobee sensors ---
    "sensor.bedroom_temperature_2":          "sensor.home_office_ecobee_temperature",
    "sensor.bedroom_temperature_3":          "sensor.home_zack_bedroom_ecobee_temperature",
    "sensor.bedroom_temperature_4":          "sensor.home_austin_bedroom_ecobee_temperature",
    "sensor.bedroom_battery":                "sensor.home_office_ecobee_battery",
    "sensor.bedroom_battery_2":              "sensor.home_zack_bedroom_ecobee_battery",
    "sensor.bedroom_battery_3":              "sensor.home_austin_bedroom_ecobee_battery",
    "sensor.kitchen_temperature":            "sensor.home_kitchen_ecobee_temperature",
    "sensor.kitchen_battery":               "sensor.home_kitchen_ecobee_battery",
    "sensor.living_room_temperature_2":      "sensor.home_living_room_ecobee_temperature",
    "sensor.living_room_battery":            "sensor.home_living_room_ecobee_battery",
    "sensor.downstairs_current_temperature": "sensor.home_downstairs_ecobee_temperature",
    "sensor.downstairs_current_humidity":    "sensor.home_downstairs_ecobee_humidity",
    "sensor.main_floor_current_temperature": "sensor.home_main_floor_ecobee_temperature",
    "sensor.main_floor_current_humidity":    "sensor.home_main_floor_ecobee_humidity",

    # --- Home: Ecobee selects ---
    "select.downstairs_current_mode":              "select.home_downstairs_ecobee_mode",
    "select.downstairs_temperature_display_units": "select.home_downstairs_ecobee_temp_units",
    "select.main_floor_current_mode":              "select.home_main_floor_ecobee_mode",
    "select.main_floor_temperature_display_units": "select.home_main_floor_ecobee_temp_units",
    "select.upstairs_current_mode":                "select.home_upstairs_ecobee_mode",
    "select.upstairs_temperature_display_units":   "select.home_upstairs_ecobee_temp_units",

    # --- Home: Ecobee buttons ---
    "button.bedroom_identify":      "button.home_office_ecobee_identify",
    "button.bedroom_identify_2":    "button.home_zack_bedroom_ecobee_identify",
    "button.bedroom_identify_3":    "button.home_austin_bedroom_ecobee_identify",
    "button.downstairs_clear_hold": "button.home_downstairs_ecobee_clear_hold",
    "button.downstairs_identify":   "button.home_downstairs_ecobee_identify",
    "button.kitchen_identify":      "button.home_kitchen_ecobee_identify",
    "button.living_room_identify":  "button.home_living_room_ecobee_identify",
    "button.main_floor_clear_hold": "button.home_main_floor_ecobee_clear_hold",
    "button.main_floor_identify":   "button.home_main_floor_ecobee_identify",
    "button.tv_room_identify":      "button.home_living_room_2_ecobee_identify",
    "button.upstairs_clear_hold":   "button.home_upstairs_ecobee_clear_hold",
    "button.upstairs_identify":     "button.home_upstairs_ecobee_identify",

    # --- Home: Samsung TV ---
    "media_player.samsung_the_frame_55_qn55ls03bdfxza": "media_player.home_living_room_samsung_frame",
    "remote.samsung_the_frame_55_qn55ls03bdfxza":       "remote.home_living_room_samsung_frame",

    # --- Home: Rachio ---
    "binary_sensor.rachio_3766_connectivity": "binary_sensor.home_rachio_connectivity",
    "binary_sensor.rachio_3766_rain":         "binary_sensor.home_rachio_rain",

    # --- Person ---
    "person.ed3766": "person.ed",

    # --- SPAN Panel A (nt-2226-c1fwg) battery/stats: fix _2_ → _a_ ---
    "binary_sensor.home_span_panel_2_battery_bess_connected":  "binary_sensor.home_span_panel_a_battery_bess_connected",
    "sensor.home_span_panel_2_battery_battery_level":          "sensor.home_span_panel_a_battery_battery_level",
    "sensor.home_span_panel_2_battery_battery_power":          "sensor.home_span_panel_a_battery_battery_power",
    "sensor.home_span_panel_2_battery_firmware_version":       "sensor.home_span_panel_a_battery_firmware_version",
    "sensor.home_span_panel_2_battery_model":                  "sensor.home_span_panel_a_battery_model",
    "sensor.home_span_panel_2_battery_nameplate_capacity":     "sensor.home_span_panel_a_battery_nameplate_capacity",
    "sensor.home_span_panel_2_battery_serial_number":          "sensor.home_span_panel_a_battery_serial_number",
    "sensor.home_span_panel_2_battery_state_of_energy":        "sensor.home_span_panel_a_battery_state_of_energy",
    "sensor.home_span_panel_2_battery_vendor":                 "sensor.home_span_panel_a_battery_vendor",
    "sensor.home_span_panel_2_dsm_state":                      "sensor.home_span_panel_a_dsm_state",
    "sensor.home_span_panel_2_feed_through_net_energy":        "sensor.home_span_panel_a_feed_through_net_energy",
    "sensor.home_span_panel_2_l1_voltage":                     "sensor.home_span_panel_a_l1_voltage",
    "sensor.home_span_panel_2_l2_voltage":                     "sensor.home_span_panel_a_l2_voltage",
    "sensor.home_span_panel_2_main_breaker_rating":            "sensor.home_span_panel_a_main_breaker_rating",
    "sensor.home_span_panel_2_main_meter_net_energy":          "sensor.home_span_panel_a_main_meter_net_energy",
    "sensor.home_span_panel_2_pv_nameplate_capacity":          "sensor.home_span_panel_a_pv_nameplate_capacity",
    "sensor.home_span_panel_2_upstream_l1_current":            "sensor.home_span_panel_a_upstream_l1_current",
    "sensor.home_span_panel_2_upstream_l2_current":            "sensor.home_span_panel_a_upstream_l2_current",
    "sensor.home_span_panel_2_vendor_cloud":                   "sensor.home_span_panel_a_vendor_cloud",
}

SPAN_DOMAINS = {"sensor", "binary_sensor", "switch", "select", "button", "update", "number"}


def build_span_renames(existing_ids):
    renames = {}
    for entity_id in existing_ids:
        domain, name = entity_id.split(".", 1)
        if domain in SPAN_DOMAINS and name.startswith("span_panel"):
            renames[entity_id] = f"{domain}.home_{name}"
    return renames


def load_env_file():
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")


def restart_ha(ha_url, token):
    result = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
         "-X", "POST", f"{ha_url}/api/services/homeassistant/restart",
         "-H", f"Authorization: Bearer {token}",
         "-H", "Content-Type: application/json",
         "--connect-timeout", "10", "--max-time", "30"],
        capture_output=True, text=True,
    )
    return result.stdout.strip() == "200"


def main():
    load_env_file()
    ha_host = os.getenv("HA_HOST", "homeassistant")
    ha_url = os.getenv("HA_URL", "http://homeassistant.local:8123")
    token = os.getenv("HA_TOKEN", "")
    dry_run = "--apply" not in sys.argv

    if not REGISTRY_LOCAL.exists():
        print(f"❌ Registry file not found at {REGISTRY_LOCAL}. Run 'make pull' first.")
        sys.exit(1)

    print("=" * 60)
    print(f"  Entity Rename Tool — {'DRY RUN' if dry_run else 'APPLYING CHANGES'}")
    print("=" * 60)
    if dry_run:
        print("  Run with --apply to execute.\n")

    with open(REGISTRY_LOCAL) as f:
        registry = json.load(f)

    entities = registry["data"]["entities"]
    existing_ids = {e["entity_id"] for e in entities}
    print(f"  Registry loaded: {len(entities)} entities\n")

    rename_map = {**RENAME_MAP, **build_span_renames(existing_ids)}

    # Only check conflicts for renames where the source entity still exists
    active_renames = {k: v for k, v in rename_map.items() if k in existing_ids}
    new_ids = set(active_renames.values())
    conflicts = new_ids & (existing_ids - set(active_renames.keys()))
    if conflicts:
        print("❌ Target entity IDs already exist (not being renamed):")
        for c in sorted(conflicts):
            print(f"   {c}")
        sys.exit(1)

    # Apply renames to registry
    applied = skipped = 0
    id_map = {}  # old_id → new_id for applied renames

    for entity in entities:
        old_id = entity["entity_id"]
        if old_id in rename_map:
            new_id = rename_map[old_id]
            if dry_run:
                print(f"  ✅ WOULD RENAME: {old_id} → {new_id}")
            else:
                entity["entity_id"] = new_id
                id_map[old_id] = new_id
            applied += 1
        else:
            skipped += 1

    not_found = set(rename_map.keys()) - existing_ids
    if not_found:
        print(f"\n  ⚠️  {len(not_found)} entities in rename map not found in registry:")
        for e in sorted(not_found):
            print(f"     {e}")

    print(f"\n  {'Would rename' if dry_run else 'Renamed'}: {applied}")
    print(f"  Unchanged:       {skipped}")

    if dry_run:
        print("\n  Run with --apply to execute.")
        return

    # Write modified registry to temp file
    tmp_path = Path("temp/core.entity_registry.modified")
    tmp_path.parent.mkdir(exist_ok=True)
    with open(tmp_path, "w") as f:
        json.dump(registry, f, separators=(",", ":"))
    print(f"\n  Modified registry written to {tmp_path}")

    # Push to HA via SSH
    print(f"  Pushing to {ha_host}:{REGISTRY_REMOTE} ...")
    result = subprocess.run(
        ["ssh", ha_host, f"cat > {REGISTRY_REMOTE}"],
        input=tmp_path.read_text(),
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  ❌ SSH push failed: {result.stderr}")
        sys.exit(1)
    print("  ✅ Registry pushed successfully.")

    # Also update local registry
    import shutil
    shutil.copy(tmp_path, REGISTRY_LOCAL)
    print("  ✅ Local registry updated.")

    # Restart HA
    print("\n  Restarting Home Assistant...")
    if token and restart_ha(ha_url, token):
        print("  ✅ Home Assistant restarting — wait ~60 seconds before using it.")
    else:
        print("  ⚠️  Could not trigger restart via API.")
        print("     Restart manually: Settings → System → Restart")

    print("\n" + "=" * 60)
    print(f"  ✅ Done! {applied} entities renamed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
