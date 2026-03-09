# Options UI Features

## Coverage

- Options chain workbench at `/stocks`
- Call/put side-by-side strike table
- Greeks columns (delta, gamma) with visual color coding
- OI movement and PCR display
- OI heatmap snapshot panel
- Strike symbol chart popup on click
- Option filters:
  - IV minimum
  - delta minimum
  - gamma minimum
  - OI minimum
  - OI change % minimum
  - volume minimum

## Responsive Behavior

- Mobile (`< md`):
  - strike rows render as cards with compact metric summary
  - direct action buttons for call/put chart
- Desktop (`>= md`):
  - full-width horizontal table with all columns
  - overflow-safe table container for large data widths

## Data Endpoints Used

- `GET /api/v1/options/chain`
- `GET /api/v1/options/metrics`
- `POST /api/v1/options/greeks/calculate`
- `GET /api/v1/strikes/{symbol}/vol/greeks`
- `GET /api/v1/options/oi/heatmap`
- `GET /api/v1/strikes/{symbol}/candles`
