# NGRS Solver - Folder Structure Guide

This document explains the new folder organization and how to use it.

## Folder Structure

```
ngrssolver/
├── input/                    # All input JSON files
│   ├── input_enhanced.json
│   ├── input_monthly_ot_test.json
│   ├── input_realistic.json
│   └── input_violation_test.json
│
├── output/                   # All solver output JSON files
│   ├── output.json
│   ├── output_enhanced.json
│   ├── output_monthly_ot.json
│   ├── output_realistic.json
│   └── (all other output files)
│
├── viewer.html              # Interactive dashboard for viewing results
├── server.py                # HTTP server with file browsing API
├── src/
│   └── run_solver.py        # Main solver entry point
├── Makefile                 # Build commands
└── start_viewer.sh          # Quick start script
```

## Usage

### 1. Running the Solver

The solver now automatically looks for input files in the `input/` folder and saves output to the `output/` folder.

**Basic usage:**
```bash
python src/run_solver.py --in input_enhanced.json --out output_enhanced.json
```

**Or using Make:**
```bash
make solve
```

### 2. Viewing Results with Interactive Dashboard

**Start the server:**
```bash
./start_viewer.sh
# OR
python server.py
# OR using Make
make server
```

Then open in your browser: **http://localhost:8000/viewer.html**

**Features:**
- Dropdown selector to browse and load all files from `output/` folder
- Real-time file listing from the server API
- Interactive dashboards for:
  - Summary statistics
  - Assignments timeline
  - Employee details
  - Violations analysis
  - Metadata inspection

### 3. File API Endpoints

The server provides REST APIs for file discovery:

- **`GET /api/output-files`** - List all JSON files in the `output/` folder
  ```json
  {
    "files": [
      {
        "name": "output_enhanced.json",
        "size": 96230,
        "modified": 1699809180.5,
        "path": "output/output_enhanced.json"
      }
    ]
  }
  ```

- **`GET /api/input-files`** - List all JSON files in the `input/` folder

### 4. Benefits of This Structure

✅ **Cleaner organization** - Separate input and output files  
✅ **Easier file management** - No clutter in root directory  
✅ **Dynamic file browsing** - HTML viewer automatically discovers new output files  
✅ **No hardcoding** - Server dynamically lists available files  
✅ **Scalability** - Easy to add more test cases and manage multiple runs  

## Example Workflow

```bash
# 1. Run the solver
python src/run_solver.py --in input_enhanced.json --out output_enhanced_v2.json

# 2. Start the server
./start_viewer.sh

# 3. Open browser to http://localhost:8000/viewer.html

# 4. Select "output_enhanced_v2.json" from the dropdown

# 5. View results in interactive dashboard
```

## Moving Existing Files

If you have output files in the root directory, move them to the `output/` folder:

```bash
mv output*.json output/
mv input*.json input/
```

## Notes

- The HTML viewer requires a running server to access the file list API
- Files must be in JSON format to appear in the file browser
- The solver automatically creates the `output/` folder if it doesn't exist
