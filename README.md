# Health Addon for Home Assistant

Custom component for tracking health parameters and medications in Home Assistant.

## Features

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
- Track inventory quantity
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

### Initial Setup
1. Go to Settings → Devices & Services → Add Integration
2. Search for "Health Addon"
3. Click Add

### Adding Health Parameters
Use the service `health_addon.add_health_parameter`:

```yaml
service: health_addon.add_health_parameter
data:
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
  name: "Metformin"
  dosage: "500mg"
  quantity: 30
```

### Logging a Dose
```yaml
service: health_addon.log_dose
data:
  medication_id: 1
```

### Updating Medication Quantity
```yaml
service: health_addon.update_quantity
data:
  medication_id: 1
  quantity: 29
```

## Automations

### Daily Medication Reminder
```yaml
automation:
  - alias: "Medication Reminder"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: notify.persistent_notification
        data:
          title: "Medication Reminder"
          message: "Time to take your morning medication!"
```

### Check Last Dose
Get the last dose time from the sensor's attributes to create alerts if a dose was missed.

## Entities

After setup, you'll find:
- Health parameter sensors (one per metric)
- Medication sensors (quantity + last taken time)

All sensors include history in their attributes, perfect for creating history graphs in Home Assistant.

## Services

| Service | Description |
|---------|-------------|
| `add_health_parameter` | Record a health parameter reading |
| `add_medication` | Add a new medication to inventory |
| `log_dose` | Log when a dose was taken |
| `update_quantity` | Update medication quantity |
| `delete_medication` | Remove a medication |
| `get_medications` | Get all medications (returns data) |
| `get_history` | Get parameter history |

## Development

```bash
# Clone repo
git clone https://github.com/GrzegorzRussek/HA.Health.Addon.git

# Copy to HA custom_components
cp -r custom_components/health_addon /path/to/ha/custom_components/
```

## License

MIT
