# GUI Smoke Checklist

Use this checklist for quick release validation on Windows after `py -m loop_calculator` starts.

## Startup

- App launches without crash.
- Main window title and logo are visible.
- Sidebar navigation can switch between `LOOPS`, `DATABASE`, and `ACCESS`.

## Loop Editing

- In `LOOPS`, click add loop and confirm a new tab appears.
- Add one row/device in a loop and set `qty`, `lead_dist`, and `interval_dist`.
- Verify summary values (`addr`, `curr`, `volt`, `lens`, `max_len`, `theo_max_len`, `rec_cable`) update.
- Close a non-last tab and confirm close confirmation works.

## Database

- Open `DATABASE`, create or edit one product, then save.
- Return to `LOOPS` and confirm the product can be selected in device list.
- Change one product customer name and verify it persists after app restart.

## Access Control

- Open `ACCESS` page and verify current role is shown.
- Try admin/factory login with current passwords and verify role text updates.
- Logout and verify protected actions are disabled again.

## Persistence

- Close app and reopen.
- Verify last workspace/tab data is restored.
- Verify edited product data still exists.
