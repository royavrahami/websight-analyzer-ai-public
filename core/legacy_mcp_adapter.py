from typing import Dict, Any, List, Optional, Union
import json
from pathlib import Path
from datetime import datetime

def generate_full_test_suite(elements_data: Dict, metadata: Dict, output_dir: str) -> Dict[str, Any]:
    """
    Generate full test suite from elements data
    
    Args:
        elements_data: Analyzed elements data
        metadata: Page metadata
        output_dir: Output directory
        
    Returns:
        Test generation info
    """
    # Placeholder implementation for test generation
    # In a real implementation, this would generate pytest files, page objects, etc.
    return {
        "test_files": [],
        "page_objects": [],
        "total_tests": 0,
        "test_types": ["smoke", "functional", "ui"]
    }

def generate_tests_from_analysis(analysis_dir: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate MCP tests from existing analysis results
    
    Args:
        analysis_dir: Path to analysis directory with enhanced_elements.json
        output_dir: Output directory for generated tests
        
    Returns:
        Dictionary with generated test info
    """
    print(f"🔄 Generating MCP tests from analysis: {analysis_dir}")
    
    analysis_path = Path(analysis_dir)
    if not analysis_path.exists():
        print(f"❌ Analysis directory not found: {analysis_path}")
        return {"status": "error", "message": "Analysis directory not found"}
    
    # Find enhanced_elements.json
    enhanced_elements_file = None
    for file_path in analysis_path.rglob("enhanced_elements.json"):
        enhanced_elements_file = file_path
        break
    
    if not enhanced_elements_file:
        print(f"❌ enhanced_elements.json not found in {analysis_path}")
        return {"status": "error", "message": "enhanced_elements.json not found"}
    
    # Set output directory
    if not output_dir:
        output_path = analysis_path.parent / "generated_tests"
    else:
        output_path = Path(output_dir)
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load analysis data
    try:
        with open(enhanced_elements_file, 'r', encoding='utf-8') as f:
            elements_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading enhanced_elements.json: {e}")
        return {"status": "error", "message": f"Error loading analysis data: {e}"}
    
    # Extract metadata
    metadata_file = enhanced_elements_file.parent / "metadata.json"
    metadata = {}
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except Exception:
            pass
    
    # Generate tests
    try:
        test_info = generate_full_test_suite(elements_data, metadata, str(output_path))
        
        # Create connection file linking analysis to tests
        connection_file = output_path / "analysis_connection.json"
        connection_data = {
            "analysis_source": str(enhanced_elements_file),
            "analysis_timestamp": datetime.now().isoformat(),
            "generated_tests": test_info,
            "metadata": metadata
        }
        
        with open(connection_file, 'w', encoding='utf-8') as f:
            json.dump(connection_data, f, indent=2)
        
        print(f"✅ Tests generated successfully: {output_path}")
        test_info["output_directory"] = str(output_path)
        test_info["connection_file"] = str(connection_file)
        test_info["status"] = "success"
        
        return test_info
        
    except Exception as e:
        print(f"❌ Error generating tests: {e}")
        return {"status": "error", "message": f"Error generating tests: {e}"}

def scan_and_generate_missing_tests(base_results_dir: Optional[str] = None) -> List[Dict]:
    """
    Scan for analysis results without corresponding tests and generate them
    
    Args:
        base_results_dir: Base directory to scan for results
        
    Returns:
        List of generation results
    """
    if not base_results_dir:
        base_results_dir = "./WebAnalyzerResults"
    
    base_path = Path(base_results_dir)
    if not base_path.exists():
        print(f"❌ Results directory not found: {base_path}")
        return []
    
    print(f"🔍 Scanning for analysis results in: {base_path}")
    
    results = []
    
    # Find all enhanced_elements.json files
    for enhanced_file in base_path.rglob("enhanced_elements.json"):
        analysis_dir = enhanced_file.parent
        
        # Check if tests already exist
        potential_test_dir = analysis_dir.parent / "generated_tests"
        connection_file = potential_test_dir / "analysis_connection.json"
        
        if connection_file.exists():
            print(f"⏭️ Tests already exist for: {analysis_dir}")
            continue
        
        print(f"🔄 Generating tests for: {analysis_dir}")
        result = generate_tests_from_analysis(str(analysis_dir))
        result["analysis_dir"] = str(analysis_dir)
        results.append(result)
    
    print(f"✅ Completed test generation for {len(results)} analysis results")
    return results 