# AWS EC2 Inventory – Legacy vs Graviton Analyzer

<div align="center">
  
![AWS EC2 Inventory](https://img.icons8.com/fluency/96/amazon-web-services.png)

## Automate EC2 Inventory Across Multiple AWS Accounts and Regions

**Updated: December 2, 2025**

[![Follow @nicoleepaixao](https://img.shields.io/github/followers/nicoleepaixao?label=Follow&style=social)](https://github.com/nicoleepaixao)
[![Star this repo](https://img.shields.io/github/stars/nicoleepaixao/aws-ec2-inventory?style=social)](https://github.com/nicoleepaixao/aws-ec2-inventory)

</div>

---

## **Overview**

This project automates the entire EC2 inventory process across multiple AWS accounts and regions, producing a **FinOps-ready Excel report** with automatic classification of legacy instances and Graviton (ARM) migration opportunities. The tool helps identify cost optimization opportunities and plan modernization initiatives.

---

## **Important Information**

### **The Challenge**

| **Aspect** | **Details** |
|------------|-------------|
| **Legacy Types** | t2, m3, m4, c3, r3 instances still in production |
| **Modern x86** | t3/t3a, m6a, r6a - newer generation alternatives |
| **Graviton (ARM)** | t4g, m6g, r7g - cost-effective ARM-based instances |
| **Manual Process** | Time-consuming and error-prone across multiple accounts |
| **Visibility Gap** | Difficult to identify optimization opportunities |

### **Key Questions Answered**

- Which instances are still running on **legacy generations**?
- Where could we migrate to **Graviton** to reduce costs?
- How many instances are **stopped** and should be decommissioned?
- What is the distribution across accounts and regions?

### **Solution Benefits**

- **Automated**: Scans all accounts and regions automatically
- **Comprehensive**: Complete inventory with classification
- **Actionable**: Excel output ready for FinOps analysis
- **Multi-Account**: Support for multiple AWS profiles
- **Time-Saving**: Minutes instead of hours of manual work

---

## **How the Script Works**

### **Process Flow**

1. **Authenticate:** Connect using one or more **AWS CLI profiles**
2. **Scan Regions:** Discover and scan **all or selected AWS regions**
3. **Parse Instance Types:** Extract Family, Generation, and Suffix from each instance type
4. **Classify:** Apply rules to mark instances as Legacy or Current
5. **Detect Graviton:** Automatically identify ARM-based instances
6. **Export Report:** Generate Excel file with complete inventory

### **Instance Type Parsing**

The script intelligently parses instance types into components:

- **Family**: `t`, `m`, `r`, `c`, `i` (instance family)
- **Generation**: `2`, `3`, `4`, `5`, `6`, `7` (generation number)
- **Suffix**: `a` (AMD), `g` (Graviton), `gd`, `gn` (Graviton variants)

### **Report Contents**

| **Field** | **Description** |
|-----------|----------------|
| **Account/Profile** | Source AWS profile or account |
| **Region** | AWS region where instance is deployed |
| **Instance ID** | Unique EC2 instance identifier |
| **Name Tag** | Instance name from tags |
| **Instance Type** | Full instance type (e.g., t3a.medium) |
| **Family Base** | Instance family and generation |
| **Graviton** | Yes/No - ARM-based instance |
| **Status** | Legacy or Current generation |
| **State** | running, stopped, terminated |
| **Launch Time** | Instance launch timestamp (UTC) |

---

## **Architecture**

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

## **Available Instance Classifications**

<div align="center">

| **Legacy** | **Modern x86** | **Graviton (ARM)** |
|:----------:|:--------------:|:------------------:|
| t2, m3, m4 | t3/t3a, m6a | t4g, m6g, m7g |
| c3, r3, i3 | c6a, r6a, i4i | c7g, r7g, im4gn |

</div>

---

## **How to Get Started**

### **Installation Process**

1. **Clone Repository:** Download the project to your local machine
   ```bash
   git clone https://github.com/nicoleepaixao/aws-ec2-inventory-legacy-graviton.git
   cd aws-ec2-inventory-legacy-graviton
   ```

2. **Create Virtual Environment:** Isolate Python dependencies
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # .venv\Scripts\activate   # Windows PowerShell
   ```

3. **Install Dependencies:** Install required Python packages
   ```bash
   pip install -r requirements.txt
   ```

![Installation Process](../images/install.png)
*Virtual Environment Setup*

4. **Configure AWS Profiles:** Set up your AWS CLI credentials in `~/.aws/config`
   ```ini
   [profile Dev]
   region = us-east-1
   output = json

   [profile Prod]
   region = us-east-1
   output = json
   ```

**Note:** Ensure your AWS profiles have appropriate EC2 read permissions before running the inventory.

---

## **Running the Inventory**

1. **Basic Execution:** Run with default profile and all regions
   ```bash
   python inventario_ec2.py
   ```

2. **Multiple Profiles:** Scan across multiple AWS accounts
   ```bash
   python inventario_ec2.py --profiles "Dev,Prod,Shared"
   ```

3. **Specific Regions:** Limit scan to selected regions
   ```bash
   python inventario_ec2.py --profiles "Dev,Prod" --regions "us-east-1,sa-east-1"
   ```

4. **Review Output:** Open the generated Excel file
   - File format: `ec2_inventory_YYYYMMDD_HHMMSS.xlsx`
   - Location: Current directory

5. **Analyze Results:** Filter and analyze using Excel features

---

## **Understanding the Output**

### **Excel Report Structure**

The generated file contains a sheet called `EC2_Inventory` with the following structure:

| Account(Profile) | Region    | InstanceId   | NameTag    | InstanceType | FamilyBase | Generation | Graviton | Status | State   | LaunchTimeUTC       |
|------------------|-----------|--------------|------------|--------------|------------|------------|----------|--------|---------|---------------------|
| Dev              | us-east-1 | i-0123456789 | vpn        | t2.micro     | t2         | 2          | Não      | Antiga | running | 2021-08-17 20:11:00 |
| Dev              | us-east-1 | i-0aaaabbbb  | grafana    | t3a.medium   | t3a        | 3          | Não      | Atual  | running | 2024-06-18 17:40:00 |
| Prod             | us-east-1 | i-0cccddddd  | wordpress  | r7g.large    | r7g        | 7          | Sim      | Atual  | running | 2024-01-09 13:25:00 |

### **Analysis Strategies**

- **Filter by Status = "Antiga"**: Identify all legacy instances requiring upgrade
- **Filter by Graviton = "Sim"**: Review current ARM-based workloads
- **Group by Account/Region**: Plan migration waves strategically
- **Filter by State = "stopped"**: Find candidates for decommissioning

---

## **Migration Recommendations**

### **Typical Upgrade Paths**

| **Current Type** | **Suggested Target** | **Benefits** |
|------------------|---------------------|--------------|
| t2.micro | t4g.small / t3.micro | Lower cost, better performance |
| t2.large | t3a.large / m7g.large | Newer generation, ARM option available |
| i3.large | i4i.large / im4gn.large | Better I/O performance and price/performance |
| r4.large | r7a.large / r7g.large | Modern memory-optimized with cost savings |
| m4.xlarge | m6a.xlarge / m7g.xlarge | Latest generation with significant improvements |

### **Migration Considerations**

- **Application Compatibility**: Test workloads on Graviton before migration
- **Cost Analysis**: Calculate potential savings using AWS Pricing Calculator
- **Performance Testing**: Benchmark applications in target environment
- **Migration Planning**: Plan migrations during maintenance windows

### **Important Reminders**

- This tool provides inventory data only; it does not perform migrations
- Always test in non-production environments first
- Review AWS documentation for instance type compatibility
- Consider using AWS Migration Hub for tracking migration progress

---

## **Use Cases**

This inventory tool is ideal for:

- **FinOps Reviews**: EC2 cost optimization and analysis
- **Graviton Migration Planning**: Identify ARM migration candidates
- **Legacy System Mapping**: Plan replatforming initiatives before EOL
- **Dashboard Integration**: Export data to QuickSight, Grafana, or Looker
- **Multi-Account Governance**: Standardize instance types across organization
- **Capacity Planning**: Understand current instance distribution

---

## **Technologies Used**

| **Technology** | **Version** | **Purpose** |
|----------------|-------------|-------------|
| Python | 3.8+ | Core scripting language |
| boto3 | Latest | AWS SDK for Python (EC2 API calls) |
| pandas | Latest | Data manipulation and analysis |
| openpyxl | Latest | Excel file generation and formatting |
| AWS CLI | Latest | Profile and credential management |

---

## **Additional Information**

For more details about AWS EC2 instance types, Graviton processors, and cost optimization strategies, refer to the following resources:

- [AWS EC2 Instance Types](https://aws.amazon.com/ec2/instance-types/) - Complete instance catalog
- [AWS Graviton](https://aws.amazon.com/ec2/graviton/) - ARM-based processors
- [AWS Cost Optimization](https://aws.amazon.com/pricing/cost-optimization/) - Best practices
- [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) - Python SDK

---

## **Future Enhancements**

| **Feature** | **Description** | **Status** |
|-------------|-----------------|------------|
| Cost Estimation | Add pricing data and calculate potential savings | Planned |
| CloudWatch Integration | Include CPU/memory metrics for rightsizing | Planned |
| Recommendations Engine | Automated migration path suggestions | In Development |
| AWS Organizations | Native multi-account support with AssumeRole | Planned |
| CI/CD Integration | Scheduled runs via GitHub Actions or AWS Lambda | Planned |
| Web Dashboard | Interactive web interface for inventory viewing | Future |

---

## **Connect & Follow**

Stay updated with AWS optimization strategies and tool updates:

<div align="center">

[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/nicoleepaixao)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?logo=linkedin&logoColor=white&style=for-the-badge)](https://www.linkedin.com/in/nicolepaixao/)
[![Medium](https://img.shields.io/badge/Medium-12100E?style=for-the-badge&logo=medium&logoColor=white)](https://medium.com/@nicoleepaixao)

</div>

---

## **Disclaimer**

Information and recommendations provided are based on AWS best practices as of December 2, 2025. AWS pricing, instance availability, and features may vary by region and change over time. Always test migrations in non-production environments and refer to official AWS documentation for the most current information.

---

<div align="center">

**Happy optimizing your AWS infrastructure!**

*Document last updated: December 2, 2025*

</div>
