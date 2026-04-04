# Health Addon for Home Assistant

Custom component for tracking health parameters and medications in Home Assistant.

## Features

### Multi-User Support
Each family member can have their own profile with:
- Individual health parameters (blood pressure, blood sugar, weight, etc.)
- Personal medication inventory and schedule
- Dashboard view across all users

### Health Parameters
Track various health metrics:
- Blood pressure (systolic/diastolic)
- Blood sugar
- Heart rate
- Temperature
- Weight
- Oxygen saturation

All parameters are stored with full history, allowing you to create charts and trends in Home Assistant.

### Medication Management
- Add medications manually or via barcode scanning
- Track inventory quantity per user
- Log when doses are taken
- Automatic reminders via Home Assistant automations
- Expiration date tracking

## Installation

### Option 1: HACS (Recommended)
1. Install [HACS](https://hacs.xyz/) if not already installed
2. Go to HACS → Integrations → "+"
3. Search for "Health Addon" and install
4. Restart Home Assistant

### Option 2: Manual Installation
1. Copy `custom_components/health_addon` folder to your Home Assistant's `custom_components` folder
2. Restart Home Assistant

## Configuration

### Initial Setup - Adding Users
1. Go to Settings → Devices & Services → Add Integration
2. Search for "Health Addon"
3. Click Add
4. Enter a unique user ID (e.g., "john", "alice") and display name
5. Repeat for each family member

Each user gets their own set of:
- Health parameter sensors
- Medication sensors
- Service data scoped to their user_id

### Adding Health Parameters
Use the service `health_addon.add_health_parameter`:

```yaml
service: health_addon.add_health_parameter
data:
  user_id: "john"          # optional, uses config entry user if omitted
  name: "blood_sugar"
  value: 120
  unit: "mg/dL"
```

Available parameter names:
- `pressure_systolic`
- `pressure_diastolic`
- `blood_sugar`
- `heart_rate`
- `temperature`
- `weight`
- `oxygen`

### Adding Medications
Use the service `health_addon.add_medication`:

```yaml
service: health_addon.add_medication
data:
  user_id: "john"          # optional
  name: "Metformin"
  dosage: "500mg"
  quantity: 30
```

### Logging a Dose
```yaml
service: health_addon.log_dose
data:
  user_id: "john"          # optional
  medication_id: 1
```

### Updating Medication Quantity
```yaml
service: health_addon.update_quantity
data:
  user_id: "john"          # optional
  medication_id: 1
  quantity: 29
```

## Automations

### Daily Medication Reminder for All Users
```yaml
automation:
  - alias: "Morning Medication Reminder"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - choose:
          - conditions:
              - condition: state
                entity_id: sensor.health_addon_medication_john_1
                below: 5
            sequence:
              - service: notify.persistent_notification
                data:
                  title: "Medication Reminder"
                  message: "John is running low on medication!"
          - conditions:
              - condition: state
                entity_id: sensor.health_addon_medication_alice_1
                below: 5
            sequence:
              - service: notify.persistent_notification
                data:
                  title: "Medication Reminder"
                  message: "Alice is running low on medication!"
```

### Dose Taken Notification
```yaml
automation:
  - alias: "Log When Medication Taken"
    trigger:
      - platform: state
        entity_id: sensor.health_addon_medication_john_1
    action:
      - service: logbook.log
        data:
          name: "Medication Taken"
          message: "John took medication"
          entity_id: sensor.health_addon_medication_john_1
```

## Entities

After setup, you'll find sensors with format:
- `sensor.health_addon_{user_id}_{parameter_name}` for health parameters
- `sensor.health_addon_medication_{user_id}_{medication_id}` for medications

All sensors include history in their attributes, perfect for creating history graphs in Home Assistant.

### Example Dashboard
```yaml
type: entities
title: Health Dashboard
show_header_toggle: false
entities:
  - type: section
    label: John's Health
  - entity: sensor.health_addon_john_blood_sugar
  - entity: sensor.health_addon_john_pressure_systolic
  - entity: sensor.health_addon_john_weight
  - type: section
    label: Alice's Health
  - entity: sensor.health_addon_alice_blood_sugar
  - entity: sensor.health_addon_alice_weight
```

## Services

| Service | Description | Parameters |
|---------|-------------|------------|
| `add_health_parameter` | Record a health parameter reading | user_id, name, value, unit |
| `add_medication` | Add a new medication to inventory | user_id, name, dosage, barcode, expiration_date, quantity |
| `log_dose` | Log when a dose was taken | user_id, medication_id |
| `update_quantity` | Update medication quantity | user_id, medication_id, quantity |
| `delete_medication` | Remove a medication | user_id, medication_id |
| `get_medications` | Get medications for current user | user_id |
| `get_all_medications` | Get all medications (admin) | - |
| `get_history` | Get parameter history | user_id, name, limit |

## Development

```bash
# Clone repo
git clone https://github.com/GrzegorzRussek/HA.Health.Addon.git

# Copy to HA custom_components
cp -r custom_components/health_addon /path/to/ha/custom_components/
```

## License

MIT
