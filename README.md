# Playwright MCP Analyzer - Professional Edition

## 🎯 Project Overview

Professional-grade automation framework combining Microsoft's MCP (Model Context Protocol) with comprehensive web analysis. This system provides accessibility-first testing, automated test generation, and production-ready QA tools.

## 📁 Project Structure

```
playwright-mcp-analyzer-new/
├── 📂 automation/           # Main automation frameworks
│   ├── master_automation.py
│   ├── mcp_enhanced_analyzer.py
│   ├── mcp_with_progress.py
│   └── batch_analyzer.py
├── 📂 integrations/         # External service integrations
│   ├── microsoft_mcp_integration.py
│   └── mcp_playwright_integration.py
├── 📂 examples/             # Example scripts and demos
│   ├── demo_enhanced_automation.py
│   ├── analyze_data_example.py
│   └── direct_test.py
├── 📂 versions/             # Alternative language versions
│   ├── enhanced_mcp_master_automation_english.py
│   └── mcp_automation_english.py
├── 📂 core/                 # Core analysis modules
│   ├── integrated_web_analyzer.py
│   ├── playwright_web_elements_analyzer.py
│   └── mcp/
├── 📂 gui/                  # Graphical interfaces
│   └── web_analyzer_gui.py
├── 📂 client/               # Client connections
│   └── mcp_client.py
├── 📂 scripts/              # Utility scripts
├── 📂 tests/                # Test files
├── 📂 docs/                 # Documentation
│   ├── AUTOMATION_GUIDE.md
│   ├── WORKFLOW_GUIDE.md
│   ├── HOW_TO_BUILD_MCP_PLAYWRIGHT.md
│   ├── DATA_LOCATIONS_MAP.md
│   └── SYSTEM_OVERVIEW.md
├── 📂 playwright_mcp_server/ # Microsoft MCP server
└── 📂 playwright-test/      # Playwright test configs
```

## 🚀 Quick Start

### Main Entry Points

1. **Enhanced Master Automation** (Primary Interface)
   ```bash
   python enhanced_master_automation.py https://example.com
   ```

2. **GUI Interface** (User-Friendly Interface)
   ```bash
   python gui/web_analyzer_gui.py
   ```

3. **Examples** (Learning and Testing)
   ```bash
   python examples/demo_enhanced_automation.py
   ```

## 🔧 Installation

```bash
# Clone the repository
git clone <repository-url>
cd playwright-mcp-analyzer-new

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

## 📊 Features

### ✅ Microsoft MCP Integration
- **Accessibility-First Analysis** - Prioritizes accessibility tree over screenshots
- **LLM Integration** - Ready for ChatGPT, Claude, and other AI models
- **Production Standards** - Microsoft-grade architecture

### ✅ Comprehensive Analysis
- **Multi-Browser Testing** - Chromium, Firefox, WebKit
- **Performance Analysis** - Load times, resource usage
- **Security Scanning** - Vulnerability detection
- **SEO Analysis** - Search engine optimization

### ✅ Automated Test Generation
- **API Tests** - Endpoint validation
- **UI Tests** - Interface interaction testing
- **Functional Tests** - Business logic validation  
- **GUI Tests** - Visual layout testing
- **E2E Tests** - Complete user journey testing

### ✅ Professional Reports
- **HTML Reports** - Interactive visual reports
- **JSON Data** - Machine-readable results
- **VS Code Integration** - IDE launch configurations
- **CI/CD Ready** - Integration with automation pipelines

## 📖 Usage Guide

### Basic Analysis
```python
import asyncio
from enhanced_master_automation import EnhancedAutomationFramework

async def run_analysis():
    # Initialize framework
    framework = EnhancedAutomationFramework("https://example.com")
    
    # Run complete analysis
    results = await framework.run_enhanced_automation(
        browsers=['chromium'],
        use_microsoft_mcp=True,
        include_ai_analysis=True
    )
    return results

# Execute the analysis
results = asyncio.run(run_analysis())
print(f"Analysis completed! Results saved to: {results.get('output_dir', 'Unknown')}")
```

### Integration Examples
```python
import asyncio
from integrations.microsoft_mcp_integration import MCPPlaywrightServer

async def run_mcp_integration():
    # Microsoft MCP Integration
    # Create MCP server
    server = MCPPlaywrightServer({'browser': 'chromium'})
    await server.start()
    
    try:
        # Navigate and analyze
        nav_result = await server.handle_tool_call("browser_navigate", {"url": "https://example.com"})
        snapshot = await server.handle_tool_call("browser_snapshot", {})
        
        print("Navigation successful!")
        print(f"Snapshot captured: {len(snapshot)} elements found")
        
    finally:
        # Clean up server
        await server.stop()

# Execute the MCP integration
asyncio.run(run_mcp_integration())
```

### GUI Interface
```python
# Launch GUI directly
import subprocess
import sys

# Run the GUI interface
subprocess.run([sys.executable, "gui/web_analyzer_gui.py"])
```

## 🎯 Key Benefits

### For QA Engineers
- **Faster Test Creation** - AI-powered test generation
- **Better Coverage** - Microsoft accessibility standards
- **Professional Output** - Enterprise-grade reports

### For Developers
- **Early Detection** - Catch issues before production
- **Accessibility Compliance** - WCAG AA/AAA standards
- **Performance Insights** - Optimization recommendations

### For Teams
- **Standardized Process** - Consistent testing approach
- **Knowledge Sharing** - Comprehensive documentation
- **Tool Integration** - Works with existing workflows

## 🔗 Integration Points

### Development Tools
- **VS Code** - Launch configurations and snippets
- **Git** - Version control integration
- **CI/CD** - Automated pipeline integration

### External Services
- **Microsoft MCP** - Latest accessibility standards
- **LLM APIs** - AI-powered analysis
- **Reporting Tools** - Custom output formats

## 📚 Documentation

- **[Automation Guide](docs/AUTOMATION_GUIDE.md)** - Complete automation tutorial
- **[Workflow Guide](docs/WORKFLOW_GUIDE.md)** - Step-by-step processes  
- **[System Overview](docs/SYSTEM_OVERVIEW.md)** - Architecture details
- **[Build Guide](docs/HOW_TO_BUILD_MCP_PLAYWRIGHT.md)** - Setup instructions
- **[Data Locations](docs/DATA_LOCATIONS_MAP.md)** - Output file reference

## 🏗️ Architecture

The system follows a modular architecture:
- **Entry Layer** - Main scripts and GUI interfaces
- **Automation Layer** - Core automation frameworks  
- **Integration Layer** - External service connectors
- **Analysis Layer** - Data processing and insights
- **Output Layer** - Reports and generated tests

## 🤝 Contributing

1. Follow the existing directory structure
2. Add comprehensive documentation
3. Include example usage
4. Maintain English language standards
5. Test with multiple browsers

## 📋 Requirements

- Python 3.8+
- Node.js 16+ (for MCP server)
- Playwright browsers
- Optional: Anthropic API key (for AI analysis)

## 🔄 Updates

The project is actively maintained with:
- Regular security updates
- New browser compatibility
- Enhanced AI capabilities
- Improved reporting features

---

**Author:** Roy Avrahami - Senior QA Automation Architect  
**License:** MIT  
**Version:** 2.0 - Professional Edition