# AWS EC2 Inventory – Legacy vs Graviton Analyzer

Automate EC2 inventory across multiple AWS accounts and regions, with automatic classification of legacy instances and Graviton (ARM) opportunities for FinOps optimization.

---

## The Problem

As AWS environments grow, they accumulate a mix of EC2 instance generations:

- **Legacy types**: t2, m3, m4, c3, r3
- **Modern x86 families**: t3/t3a, m6a, r6a
- **Graviton (ARM) instances**: t4g, m6g, r7g

Without a clear inventory, it's difficult to answer:

- Which instances are still running on **legacy generations**?
- Where could we migrate to **Graviton** to reduce costs?
- How many instances are **stopped** and should be decommissioned?

Manually collecting this information across multiple AWS profiles and regions is time-consuming and error-prone.

**This project automates the entire EC2 inventory process** and produces a FinOps-ready Excel report with legacy vs modern vs Graviton classification.

---

## How It Works

Using Python and `boto3`, this project:

1. Authenticates using one or more **AWS CLI profiles**
2. Scans **all or selected regions** for EC2 instances
3. Parses each `InstanceType` into:
   - **Family** (e.g., `t`, `m`, `r`)
   - **Generation** (e.g., `2`, `3`, `6`, `7`)
   - **Suffix** (e.g., `a`, `g`, `gd`, `gn`)
4. Applies classification rules to:
   - Mark instances as **Legacy** (e.g., `t2`, `m3`, `m4`, `c3`, `r3`)
   - Identify **Graviton** instances (e.g., `t4g`, `m6g`, `r7g`, `im4gn`, `x2gd`)
5. Exports everything to an **Excel (.xlsx)** report

### Report Includes

- Account/Profile
- Region
- Instance ID
- Name tag
- Instance type (family/generation)
- **Graviton: Yes/No**
- **Status: Legacy/Current**
- State (running, stopped)
- Launch time (UTC)

---

## Architecture

```text
┌───────────────────────────┐      ┌───────────────────────────┐
│   AWS CLI Profiles        │      │        AWS Accounts       │
│   (~/.aws/config)         │      │ (EC2 in multiple regions) │
└─────────────┬─────────────┘      └──────────────┬────────────┘
              │                                   │
              │ boto3 Session / AssumeRole        │
              │                                   │
      ┌───────▼───────────────────────────────────▼───────────┐
      │                Python Inventory Script                │
      │  - boto3 EC2 describe_instances + paginator           │
      │  - Parse instance type (family/generation/suffix)     │
      │  - Classify: Legacy vs Current                        │
      │  - Detect: Graviton vs non-Graviton                   │
      └───────┬───────────────────────────────────┬───────────┘
              │                                   │
              │ pandas DataFrame                  │
              │                                   │
      ┌───────▼───────────────────────────────────▼───────────┐
      │                    Excel Report (.xlsx)               │
      │  - One row per EC2 instance                           │
      │  - Filters by account, region, status, Graviton       │
      │  - Ready for FinOps / cost review                     │
      └───────────────────────────────────────────────────────┘
```

---

## Project Structure

```text
.
├── inventario_ec2.py              # Main inventory script
├── requirements.txt               # Python dependencies
├── README.md                      # Project documentation
└── .gitignore                     # Ignored files (venv, Excel outputs, etc.)
```

---

## ⚡ Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/<your-user>/aws-ec2-inventory-legacy-graviton.git
cd aws-ec2-inventory-legacy-graviton
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows PowerShell
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```text
boto3
pandas
openpyxl
```

### 4. Configure your AWS CLI profiles

In `~/.aws/config`:

```ini
[profile Dev]
region = us-east-1
output = json

[profile Prod]
region = us-east-1
output = json
```

You can also use SSO/assume-role profiles as usual.

### 5. Run a basic inventory (default profile, all regions)

```bash
python inventario_ec2.py
```

This generates a file like: `ec2_inventory_20251130_173000.xlsx`

### 6. Run inventory for multiple profiles

```bash
python inventario_ec2.py --profiles "Dev,Prod,Shared"
```

Results from all profiles will be consolidated into a single Excel file.

### 7. Limit to specific regions

```bash
python inventario_ec2.py \
  --profiles "Dev,Prod" \
  --regions "us-east-1,sa-east-1"
```

Useful for quick views of regions where you actually deploy workloads.

---

## Sample Output

The generated Excel file contains a sheet called `EC2_Inventory`:

| Account(Profile) | Region    | InstanceId      | NameTag         | InstanceType | FamilyBase | Generation | Graviton | Status | State   | LaunchTimeUTC        |
|------------------|-----------|-----------------|-----------------|--------------|------------|------------|----------|--------|---------|----------------------|
| Dev              | us-east-1 | i-0123456789    | vpn           | t2.micro     | t2         | 2          | Não      | Antiga | running | 2021-08-17 20:11:00  |
| Dev              | us-east-1 | i-0aaaabbbb     | grafana         | t3a.medium   | t3a        | 3          | Não      | Atual  | running | 2024-06-18 17:40:00  |
| Prod             | us-east-1 | i-0cccddddd     | wordpress | r7g.large    | r7g        | 7          | Sim      | Atual  | running | 2024-01-09 13:25:00  |

### Analysis Options

- **Filter by Status = Antiga**: See all legacy instances (t2, m3, m4, c3, r3, etc.)
- **Filter by Graviton = Sim**: Identify all Graviton workloads
- **Group by Account(Profile)** or **Region**: Plan modernization waves

---

## Use Cases

- Preparing **FinOps reviews** focused on EC2 optimization
- Identifying targets for **Graviton migrations**
- Mapping **legacy generations** prior to replatforming
- Building dashboards (QuickSight, Grafana, Looker) on top of exported data
- Planning **modernization waves** by account or region

---

## Typical Migration Recommendations

This inventory enables data-driven migration decisions:

| Current Type | Suggested Target       | Notes                          |
|--------------|------------------------|--------------------------------|
| t2.micro     | t4g.small / t3.micro   | Lower cost, better performance |
| t2.large     | t3a.large / m7g.large  | Newer generation, ARM option   |
| i3.large     | i4i.large / im4gn.large| Better IO and price/performance|
| r4.large     | r7a.large / r7g.large  | Modern memory-optimized        |

**Note**: This project provides the inventory data; it does not perform migrations automatically.

---

## Technologies Used

- **Python 3.8+**
- **boto3** - AWS API calls (EC2)
- **pandas** - Data manipulation
- **openpyxl** - Excel export
- **AWS CLI profiles** - Multi-account access

---

## Next Steps / Enhancement Ideas

- Add a second Excel sheet with **RecommendedTargetType** per instance
- Enrich inventory with **pricing data** (on-demand hourly cost)
- Cross-reference with **CloudWatch metrics** (CPU, memory) for rightsizing
- Integrate with **AWS Organizations** + AssumeRole for full multi-account coverage
- **Containerize** the script (Docker) and schedule it (GitHub Actions, ECS task)
- Add **cost savings estimates** for Graviton migrations
- Export to **CSV/JSON** for integration with other tools

---

## License

MIT License