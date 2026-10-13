# Carrier ClassiCOOL Engineering Suite ❄️

A professional-grade HVAC selection and CAD automation tool designed for MEP engineers. This suite streamlines the process of selecting Carrier evaporator models based on technical requirements and automates the generation of high-precision DXF CAD blocks for shop drawings.

## 🏗️ System Architecture

The project follows a modular design to ensure maintainability and testability:

- **`src/carrier_tool/main.py`**: Modern Dashboard UI built with `tkinter` and `ttk`, focusing on UX/UI Pro Max principles.
- **`src/carrier_tool/logic.py`**: Core engineering logic. Implements a **weighted scoring system** to find the best matching unit, specifically optimized for the `QDMT/QDMA` series.
- **`src/carrier_tool/exporter.py`**: CAD automation engine using `ezdxf` to generate precise geometry based on official Carrier technical catalogs.
- **`src/carrier_tool/database.py`**: SQLite wrapper for efficient data retrieval of performance and electrical specs.

## 🚀 Technical Highlights

### 🧠 Smart Matching Algorithm
Unlike basic filtering, this tool uses a scoring mechanism:
`Score = (Capacity Difference) + (ESP Penalty * 10) + (Series Bonus)`
This ensures that if an exact match isn't found, the most technically viable alternative (especially from the `QDMT` series) is suggested.

### 📐 CAD Automation
The exporter doesn't just draw boxes; it implements:
- **Exact Geometry**: Dimensions mapped directly from official PDF catalogs.
- **Technical Layers**: Proper layer management (`HVAC-AHU-OUTLINE`, `HVAC-AHU-PIPES`, etc.).
- **Dynamic Attributes**: CAD blocks include editable attributes for Model, Capacity, CFM, and Electrical data.

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10+
- `ezdxf` library

### Quick Start
1. Clone the repository:
   ```bash
   git clone https://github.com/[username]/Carrier_Selection_Tool.git
   cd Carrier_Selection_Tool
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   - Windows: Double-click `Run_Carrier_Selector.bat`
   - Terminal: `python src/carrier_tool/main.py`

## 🧪 Quality Assurance
- **TDD**: Core logic is backed by a comprehensive test suite in `tests/`.
- **Independent Review**: Code has been audited for security (SQL injection) and stability (I/O error handling).
- **PDF Verified**: All dimensions and performance data are cross-referenced with official Carrier technical manuals.
