# 🚀 **WebSight Analyzer - Professional Edition**

[![GitHub License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-brightgreen.svg)](https://python.org)
[![Playwright](https://img.shields.io/badge/playwright-integrated-orange.svg)](https://playwright.dev)
[![MCP](https://img.shields.io/badge/MCP-integrated-purple.svg)](https://github.com/microsoft/mcp)

## 🎯 **Project Overview**

**WebSight Analyzer** is a professional-grade automation framework for comprehensive web analysis and testing. This system integrates multiple technologies including Playwright, Microsoft's MCP (Model Context Protocol), and AI-powered automation to provide accessibility-first testing, automated test generation, API hunting, and production-ready QA tools.

### ✨ **Key Features**

- 🕷️ **Multi-Page Web Crawling** - Analyze entire websites systematically
- 🕵️ **API Hunter** - Automatic API discovery and test generation
- 🤖 **QA Automation** - AI-powered test suite generation
- 🎨 **Professional GUI** - User-friendly interface for all operations
- 📊 **Comprehensive Reports** - HTML, CSV, and interactive visualizations
- ♿ **Accessibility Focus** - WCAG compliance and screen reader support
- 🧪 **Test Generation** - Automated functional, negative, and API tests
- 🔧 **MCP Integration** - Microsoft Model Context Protocol support

## 🚀 **Quick Start**

### Prerequisites

```bash
# Install Python 3.8+
# Install Node.js 16+
# Install Git
```

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/royavrahami/websight-analyzer-ai-public.git
cd websight-analyzer-ai-public
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Start the GUI:**
```bash
python gui/web_analyzer_gui.py
```

### 🎯 **Main Entry Points**

#### 1. **🖥️ Professional GUI** (Recommended)
```bash
python gui/web_analyzer_gui.py
```
- Complete visual interface
- Real-time progress tracking
- Interactive results display
- Multi-tab analysis management

#### 2. **📱 Command Line Interface**
```bash
python scripts/working_crawler.py -u https://example.com -o results/
```

#### 3. **🔧 Direct Core Integration**
```python
from core.integrated_web_analyzer import IntegratedWebElementAnalyzer

analyzer = IntegratedWebElementAnalyzer(headless=True)
output_dir = analyzer.analyze_url("https://example.com")
```

## 📁 **Project Structure**

```
websight-analyzer/
├── 📂 gui/                  # 🖥️ Professional GUI Interface
│   └── web_analyzer_gui.py  # Main GUI application
├── 📂 core/                 # 🔧 Core Analysis Modules
│   ├── integrated_web_analyzer.py
│   ├── playwright_web_elements_analyzer.py
│   ├── agents/              # 🤖 AI Agents
│   │   ├── api_hunter_agent.py
│   │   └── api_hunter_integration.py
│   └── automated_qa_orchestrator.py
├── 📂 scripts/              # 📱 Command Line Tools
│   ├── working_crawler.py   # Multi-page crawler
│   ├── crawl_analyze.py     # Analysis scripts
│   └── scrapy_integration.py
├── 📂 playwright_mcp_server/ # 🔗 Microsoft MCP Server
├── 📂 docs/                 # 📚 Documentation
│   ├── AUTOMATION_GUIDE.md
│   ├── WORKFLOW_GUIDE.md
│   ├── HOW_TO_BUILD_MCP_PLAYWRIGHT.md
│   ├── DATA_LOCATIONS_MAP.md
│   └── SYSTEM_OVERVIEW.md
├── 📂 integrations/         # 🔌 External Integrations
├── 📂 client/               # 🌐 Client Connections
└── 📂 playwright-test/      # 🧪 Test Configurations
```

## 🎨 **Features Overview**

### 🕷️ **Multi-Page Web Crawling**
- Systematic website analysis
- Configurable depth and page limits
- Robots.txt compliance
- Visual progress tracking

### 🕵️ **API Hunter**
- Automatic API endpoint discovery
- Real-time network traffic analysis
- Automated test generation
- Performance metrics

### 🤖 **QA Automation**
- AI-powered test suite generation
- Functional, negative, and accessibility tests
- Configurable test counts per category
- Ready-to-run pytest templates

### 🎯 **Professional GUI**
- Dark/light theme
- Real-time logging
- Interactive results tables
- Hyperlinked file navigation
- Progress indicators

## 🛠️ **Usage Examples**

### GUI Mode (Recommended)
1. Run: `python gui/web_analyzer_gui.py`
2. Enter target URL
3. Configure options (crawling, API hunting, QA automation)
4. Click "START ANALYSIS"
5. Monitor progress in real-time
6. Explore results in the "Results" tab

### Command Line Mode
```bash
# Basic analysis
python scripts/working_crawler.py -u https://example.com -o results/

# With crawling
python scripts/working_crawler.py -u https://example.com -o results/ -p 20 -d 3

# With headless mode
python scripts/working_crawler.py -u https://example.com -o results/ --headless
```

## 📊 **Output Files**

Each analysis generates:
- `📊 analysis_report.html` - Interactive dashboard
- `📋 all_elements.csv` - Structured data export
- `🐍 page_object.py` - Playwright automation class
- `🎯 selectors.py` - Element selector constants
- `🧪 test_template.py` - Ready-to-use test templates
- `🕵️ test_generated_apis.py` - API tests (if API Hunter enabled)
- `📸 screenshot.png` - Full page capture
- `📄 README.md` - Analysis summary

## 🔧 **Configuration**

### Environment Variables
```bash
# Optional: Set API keys for enhanced features
export OPENAI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"
```

### GUI Settings
- **Crawling**: Enable multi-page analysis
- **API Hunter**: Automatic API discovery
- **QA Automation**: AI test generation
- **Output Format**: HTML, CSV, JSON options

## 🧪 **Testing**

Run the included tests:
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_core.py
pytest tests/test_gui.py
pytest tests/test_integrations.py
```

## 🚀 **Advanced Features**

### MCP Integration
- Microsoft Model Context Protocol support
- Enhanced accessibility analysis
- Advanced element detection
- AI-powered insights

### API Hunter
- Real-time network monitoring
- Automatic endpoint discovery
- Performance analysis
- Test generation

### QA Automation
- Functional test generation
- Negative test scenarios
- Accessibility validation
- Load testing support

## 📚 **Documentation**

Comprehensive guides available in the `docs/` folder:
- [📖 Automation Guide](docs/AUTOMATION_GUIDE.md)
- [🔄 Workflow Guide](docs/WORKFLOW_GUIDE.md)  
- [🔧 MCP Build Guide](docs/HOW_TO_BUILD_MCP_PLAYWRIGHT.md)
- [📍 Data Locations](docs/DATA_LOCATIONS_MAP.md)
- [📋 System Overview](docs/SYSTEM_OVERVIEW.md)

## 🤝 **Contributing**

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 **Links**

- [GitHub Repository](https://github.com/royavrahami/websight-analyzer-ai-public)
- [Issue Tracker](https://github.com/royavrahami/websight-analyzer-ai-public/issues)
- [Documentation](docs/)
- [Official Website](https://royavrahami.github.io/websight-analyzer-ai-public/)

## 🙏 **Acknowledgments**

- Microsoft MCP Team
- Playwright Community
- Python Testing Community
- Open Source Contributors

---

## 🎯 **Legacy Content**

> The content below is from the original README and maintained for reference.

### Main Entry Points

1. **Enhanced Master Automation** (Primary Interface)