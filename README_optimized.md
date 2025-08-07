# Optimized Shift Scheduler Server

A single-file, optimized shift scheduling server using OR-Tools CP-SAT solver with proper Korean encoding support and nursing constraints.

## Features

- **Single File Implementation**: All functionality in one Python file
- **OR-Tools CP-SAT Solver**: Fast constraint satisfaction solving
- **Korean Encoding Support**: UTF-8, CP949, latin-1 fallback encoding
- **Python-Pro Standards**: Type hints, dataclasses, proper error handling
- **Nursing Constraints**: Newbie night shift restrictions, night-after-off rules
- **Protocol Compatibility**: Supports both C++ and Python client protocols
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements_optimized.txt
```

### 2. Start Server
```bash
python shift_server_optimized.py
```
Server starts on `127.0.0.1:6004`

### 3. Test Server
```bash
python test_optimized_server.py
```

## Request Format

### C++ Protocol Format
```json
{
  "protocol": "py_gen_timetable",
  "data": {
    "staff_data": {
      "staff": [
        {
          "name": "김간호사",
          "staff_id": 1001,
          "grade": 3,
          "total_hours": 195
        }
      ]
    },
    "position": "간호",
    "target_month": "2025-09",
    "custom_rules": {
      "shifts": ["Day", "Evening", "Night", "Off"],
      "shift_hours": {
        "Day": 8,
        "Evening": 8,
        "Night": 8,
        "Off": 0
      },
      "night_shifts": ["Night"],
      "off_shifts": ["Off"]
    }
  }
}
```

### Python Direct Format
```json
{
  "staff_data": {
    "staff": [...]
  },
  "position": "간호",
  "target_month": "2025-09",
  "custom_rules": {...}
}
```

## Response Format

### Success Response
```json
{
  "protocol": "py_gen_schedule",
  "resp": "success",
  "data": [
    {
      "date": "2025-09-01",
      "shift": "Day",
      "hours": 8,
      "people": [
        {
          "name": "김간호사",
          "staff_id": 1001,
          "grade": 3
        }
      ]
    }
  ]
}
```

### Error Response
```json
{
  "protocol": "py_gen_schedule",
  "resp": "fail",
  "data": [],
  "error": "Error message"
}
```

## Supported Positions

### 간호 (Nursing)
- Newbie no night shifts (grade 5)
- Night shift followed by off day
- Maximum 209 hours per month

### 소방 (Firefighting)  
- 24-hour duty shifts
- Mandatory off day after duty
- 6-15 duty shifts per month
- Maximum 190 hours per month

### default
- Basic constraints only
- Maximum 180 hours per month

## Shift Detection

### Explicit Specification (Recommended)
```json
"custom_rules": {
  "night_shifts": ["Night", "야간"],
  "off_shifts": ["Off", "휴무"]
}
```

### Auto-Detection
Server automatically detects night and off shifts based on keywords:

**Night Keywords**: night, nocturnal, 야간, 밤, 심야
**Off Keywords**: off, rest, free, 휴무, 쉼, 오프
**Abbreviations**: n→night, o→off, etc.

## Architecture

### Core Components
- `Staff`: Data class for staff member information
- `ShiftRules`: Shift configuration and constraints
- `PositionRules`: Position-specific rules
- `ShiftScheduler`: OR-Tools CP-SAT scheduling logic
- `ShiftSchedulerServer`: TCP server implementation
- `RequestValidator`: Input validation and parsing

### Constraint Types
1. **Basic Constraints**: One shift per person per day, minimum coverage
2. **Position Constraints**: Grade restrictions, hour limits, night-after-off
3. **Specialized Constraints**: Firefighter duty cycles, nursing newbie rules

## Error Handling

- **Input Validation**: Comprehensive parameter validation
- **Encoding Fallback**: Multiple encoding attempts for Korean text
- **Graceful Failures**: Proper error responses for unsolvable problems
- **Timeout Protection**: 30-second solver timeout to prevent hanging

## Logging

Logs include:
- Client connections and requests
- Constraint application progress
- Solver status and timing
- Error details and stack traces

Log level can be adjusted in the source code logging configuration.

## Performance

- **Solver Timeout**: 30 seconds maximum
- **Memory Efficient**: Single file, minimal dependencies
- **Korean Support**: Proper UTF-8/CP949 handling
- **Concurrent Clients**: Handles multiple clients sequentially

## Development Notes

### Dependencies
- `ortools>=9.5.0`: CP-SAT constraint solver
- Standard library only (no external services)

### Code Style
- Python-pro standards with type hints
- Dataclasses for structured data
- Comprehensive error handling
- Clean separation of concerns

### Extensibility
- Easy to add new position types in `POSITION_RULES`
- Modular constraint system
- Pluggable validation logic

## Troubleshooting

### Server Won't Start
- Check if port 6004 is available
- Verify OR-Tools installation: `pip list | grep ortools`

### Encoding Issues
- Server tries UTF-8 → CP949 → latin-1 automatically
- Check client is sending proper JSON format

### No Schedule Found
- Verify staff count is sufficient (minimum 3 recommended)
- Check total work hours vs. required coverage
- Review newbie restrictions for nursing positions

### Performance Issues
- Increase solver timeout in `SOLVER_TIMEOUT_SECONDS`
- Reduce number of staff or days for testing
- Check constraint complexity and simplify if needed