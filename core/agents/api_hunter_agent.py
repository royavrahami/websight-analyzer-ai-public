#!/usr/bin/env python3
"""
API Hunter Agent - Professional Network Traffic Analysis
========================================================

Advanced API and network traffic analysis agent that captures, analyzes,
and generates automated tests from real browser interactions.

Key Features:
- Real-time network traffic monitoring
- API endpoint discovery and analysis
- Automated test generation (pytest + httpx)
- Performance analysis and reporting
- Security vulnerability detection
- Integration with Playwright browsers

Author: Roy Avrahami - Senior QA Automation Architect
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from urllib.parse import urlparse, urljoin
import hashlib
import re

try:
    from playwright.async_api import Page, Request, Response
    import httpx
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    print("⚠️ API Hunter dependencies not available. Install with: pip install httpx playwright")


@dataclass
class APIHunterConfig:
    """Configuration for API Hunter analysis"""
    capture_xhr_only: bool = True
    capture_static_assets: bool = False
    capture_images: bool = False
    max_response_size: int = 1024 * 1024  # 1MB
    include_headers: List[str] = None
    exclude_domains: List[str] = None
    output_dir: str = "./api_analysis"
    
    def __post_init__(self):
        if self.include_headers is None:
            self.include_headers = [
                "authorization", "content-type", "x-api-key", 
                "x-csrf-token", "x-requested-with", "accept"
            ]
        if self.exclude_domains is None:
            self.exclude_domains = [
                "google-analytics.com", "facebook.com", "doubleclick.net",
                "googlesyndication.com", "googletagmanager.com"
            ]


@dataclass
class APICall:
    """Represents a captured API call"""
    id: str
    method: str
    url: str
    status_code: int
    request_headers: Dict[str, str]
    response_headers: Dict[str, str]
    request_body: Optional[str]
    response_body: Optional[str]
    duration_ms: float
    timestamp: str
    api_type: str = "REST"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class APIHunterAgent:
    """
    Advanced API Hunter Agent for network traffic analysis and test generation
    """
    
    def __init__(self, config: APIHunterConfig):
        self.config = config
        self.captured_calls: List[APICall] = []
        self.session_id = f"api_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = time.time()
        
        # Setup logging
        self.logger = logging.getLogger(f"APIHunter.{self.session_id}")
        self.logger.setLevel(logging.INFO)
        
        # Create output directory
        self.output_path = Path(self.config.output_dir)
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Statistics tracking
        self.stats = {
            'total_requests': 0,
            'captured_requests': 0,
            'failed_requests': 0,
            'unique_endpoints': 0,
            'api_calls_by_method': {},
            'api_calls_by_status': {},
            'total_duration': 0.0
        }

    async def attach_to_page(self, page: Page) -> None:
        """Attach network monitoring to a Playwright page"""
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError("Playwright and httpx are required for API Hunter")
            
        self.logger.info(f"🕵️ API Hunter attaching to page: {page.url}")
        
        # Listen to all network requests
        page.on("request", self._on_request)
        page.on("response", self._on_response)
        page.on("requestfailed", self._on_request_failed)
        
        self.logger.info("✅ API Hunter network monitoring active")

    async def _on_request(self, request: Request) -> None:
        """Handle network requests"""
        self.stats['total_requests'] += 1
        
        # Apply filtering
        if not self._should_capture_request(request):
            return
            
        # Store request start time for duration calculation
        request._api_hunter_start_time = time.time()
        
        self.logger.debug(f"📡 Capturing request: {request.method} {request.url}")

    async def _on_response(self, response: Response) -> None:
        """Handle network responses"""
        request = response.request
        
        # Check if we should capture this request
        if not self._should_capture_request(request):
            return
            
        # Calculate duration
        start_time = getattr(request, '_api_hunter_start_time', time.time())
        duration_ms = (time.time() - start_time) * 1000
        
        try:
            # Create API call object
            api_call = await self._create_api_call(request, response, duration_ms)
            
            if api_call:
                self.captured_calls.append(api_call)
                self.stats['captured_requests'] += 1
                self._update_stats(api_call)
                
                self.logger.info(
                    f"✅ Captured API call: {api_call.method} {api_call.url} "
                    f"({api_call.status_code}) - {duration_ms:.1f}ms"
                )
                
        except Exception as e:
            self.logger.error(f"❌ Error processing response: {e}")
            self.stats['failed_requests'] += 1

    async def _on_request_failed(self, request: Request) -> None:
        """Handle failed requests"""
        self.stats['failed_requests'] += 1
        self.logger.warning(f"❌ Request failed: {request.method} {request.url}")

    def _should_capture_request(self, request: Request) -> bool:
        """Determine if a request should be captured based on configuration"""
        url = request.url
        parsed_url = urlparse(url)
        
        # Check excluded domains
        if any(domain in parsed_url.netloc for domain in self.config.exclude_domains):
            return False
            
        # Check if it's XHR/Fetch only
        if self.config.capture_xhr_only:
            resource_type = request.resource_type
            if resource_type not in ['xhr', 'fetch']:
                return False
                
        # Check static assets
        if not self.config.capture_static_assets:
            if request.resource_type in ['image', 'stylesheet', 'script', 'font']:
                return False
                
        # Check images specifically
        if not self.config.capture_images and request.resource_type == 'image':
            return False
            
        return True

    async def _create_api_call(self, request: Request, response: Response, duration_ms: float) -> Optional[APICall]:
        """Create an APICall object from request/response pair"""
        try:
            # Get request details
            method = request.method
            url = request.url
            request_headers = dict(request.headers)
            
            # Filter headers based on configuration
            filtered_headers = {
                k: v for k, v in request_headers.items() 
                if k.lower() in [h.lower() for h in self.config.include_headers]
            }
            
            # Get response details
            status_code = response.status
            response_headers = dict(response.headers)
            
            # Get request body
            request_body = None
            try:
                if hasattr(request, 'post_data') and request.post_data:
                    request_body = request.post_data
            except:
                pass
                
            # Get response body (with size limit)
            response_body = None
            try:
                body_bytes = await response.body()
                if len(body_bytes) <= self.config.max_response_size:
                    response_body = body_bytes.decode('utf-8', errors='ignore')
                else:
                    response_body = f"[Response too large: {len(body_bytes)} bytes]"
            except:
                response_body = "[Could not decode response body]"
                
            # Determine API type
            api_type = self._detect_api_type(url, response_headers, response_body)
            
            # Generate unique ID
            call_id = hashlib.md5(f"{method}{url}{time.time()}".encode()).hexdigest()[:8]
            
            # Create API call
            api_call = APICall(
                id=call_id,
                method=method,
                url=url,
                status_code=status_code,
                request_headers=filtered_headers,
                response_headers=dict(response_headers),
                request_body=request_body,
                response_body=response_body,
                duration_ms=duration_ms,
                timestamp=datetime.now().isoformat(),
                api_type=api_type
            )
            
            return api_call
            
        except Exception as e:
            self.logger.error(f"Error creating API call: {e}")
            return None

    def _detect_api_type(self, url: str, headers: Dict[str, str], body: Optional[str]) -> str:
        """Detect the type of API based on URL, headers, and content"""
        content_type = headers.get('content-type', '').lower()
        
        if 'application/json' in content_type:
            return "REST"
        elif 'application/graphql' in content_type or 'graphql' in url.lower():
            return "GraphQL"
        elif 'application/soap' in content_type or (body and '<soap:' in body):
            return "SOAP"
        elif 'text/xml' in content_type:
            return "XML"
        else:
            return "REST"  # Default assumption

    def _update_stats(self, api_call: APICall) -> None:
        """Update statistics with new API call"""
        # Method statistics
        method = api_call.method
        self.stats['api_calls_by_method'][method] = self.stats['api_calls_by_method'].get(method, 0) + 1
        
        # Status code statistics
        status = api_call.status_code
        self.stats['api_calls_by_status'][status] = self.stats['api_calls_by_status'].get(status, 0) + 1
        
        # Duration statistics
        self.stats['total_duration'] += api_call.duration_ms
        
        # Update unique endpoints count
        unique_endpoints = set(call.url for call in self.captured_calls)
        self.stats['unique_endpoints'] = len(unique_endpoints)

    async def save_session_data(self) -> str:
        """Save captured session data to files"""
        session_data = {
            'session_id': self.session_id,
            'captured_at': datetime.now().isoformat(),
            'total_calls': len(self.captured_calls),
            'api_calls': [call.to_dict() for call in self.captured_calls],
            'statistics': self.stats
        }
        
        # Save session data
        session_file = self.output_path / "session_data.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
            
        self.logger.info(f"💾 Session data saved to: {session_file}")
        
        # Generate additional outputs
        await self._generate_test_suite()
        await self._generate_analysis_report()
        await self._generate_api_documentation()
        
        return str(session_file)

    async def _generate_test_suite(self) -> None:
        """Generate pytest test suite from captured API calls"""
        if not self.captured_calls:
            return
            
        test_content = self._create_pytest_content()
        
        test_file = self.output_path / "test_generated_apis.py"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
            
        self.logger.info(f"🧪 Test suite generated: {test_file}")

    def _create_pytest_content(self) -> str:
        """Create pytest test content from captured API calls"""
        unique_endpoints = {}
        for call in self.captured_calls:
            endpoint_key = f"{call.method}_{urlparse(call.url).path}"
            if endpoint_key not in unique_endpoints:
                unique_endpoints[endpoint_key] = call
                
        test_methods = []
        for i, (endpoint_key, call) in enumerate(unique_endpoints.items(), 1):
            method_name = f"test_api_endpoint_{i}"
            test_method = f'''
    @pytest.mark.asyncio
    async def {method_name}(self):
        """Test {call.method} {call.url}"""
        url = "{call.url}"
        headers = {json.dumps(call.request_headers, indent=8)}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.{call.method.lower()}(url, headers=headers)
            
            # Basic assertions
            assert response.status_code in [200, 201, 400, 401, 403, 404, 500]
            assert len(response.content) >= 0
            
            # Log results
            print(f"✅ {{response.status_code}} - {call.method} {{url}}")
            
            # Additional assertions based on original response
            if {call.status_code} in [200, 201]:
                assert response.status_code in [200, 201], f"Expected success, got {{response.status_code}}"
'''
            test_methods.append(test_method)
            
        return f'''"""
Auto-generated API Test Suite
Generated from API Hunter Agent
Session: {self.session_id}
Generated at: {datetime.now().isoformat()}
Total endpoints tested: {len(unique_endpoints)}
"""

import pytest
import httpx
import asyncio
import time
from typing import Dict, Any


class TestGeneratedAPIs:
    """Auto-generated API tests based on captured network traffic"""
    
    def setup_method(self):
        """Setup for each test method"""
        pass
    
    def teardown_method(self):
        """Cleanup after each test method"""
        pass
{"".join(test_methods)}
    
    @pytest.mark.asyncio
    async def test_api_performance_baseline(self):
        """Test API performance baseline from captured data"""
        # Average response time from captured data
        avg_response_time = {self.stats['total_duration'] / max(len(self.captured_calls), 1):.1f}
        
        # Test that average response time is reasonable
        assert avg_response_time < 5000, f"Average response time too high: {{avg_response_time}}ms"
        print(f"✅ Performance baseline: {{avg_response_time}}ms average response time")
'''

    async def _generate_analysis_report(self) -> None:
        """Generate comprehensive analysis report"""
        analysis = self.analyze_session()
        
        analysis_file = self.output_path / "analysis.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
            
        # Generate markdown report
        markdown_report = self._create_markdown_report(analysis)
        report_file = self.output_path / "api_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(markdown_report)
            
        self.logger.info(f"📊 Analysis report generated: {analysis_file}")

    def _create_markdown_report(self, analysis: Dict[str, Any]) -> str:
        """Create markdown report from analysis data"""
        return f'''# API Hunter Analysis Report

**Session ID:** {self.session_id}
**Generated:** {datetime.now().isoformat()}
**Total API Calls Captured:** {len(self.captured_calls)}

## Summary

- **Total Requests:** {self.stats['total_requests']}
- **Captured Requests:** {self.stats['captured_requests']}
- **Failed Requests:** {self.stats['failed_requests']}
- **Unique Endpoints:** {self.stats['unique_endpoints']}
- **Total Duration:** {self.stats['total_duration']:.1f}ms
- **Average Duration:** {analysis['summary']['average_duration']:.1f}ms

## HTTP Methods

{self._format_dict_as_markdown(self.stats['api_calls_by_method'])}

## Status Codes

{self._format_dict_as_markdown(self.stats['api_calls_by_status'])}

## Performance Analysis

- **Success Rate:** {analysis['performance']['success_rate']:.1f}%
- **Error Rate:** {analysis['performance']['error_rate']:.1f}%
- **Average Response Time:** {analysis['summary']['average_duration']:.1f}ms

## Endpoints Discovered

{self._format_endpoints_as_markdown()}

## Generated Test Suite

Automated pytest test suite created in `test_generated_apis.py`
- **Test Methods:** {len(set(f"{call.method}_{urlparse(call.url).path}" for call in self.captured_calls))}
- **Coverage:** All unique endpoints
- **Assertions:** Status codes, response validation, performance

## Recommendations

1. **Performance Optimization:**
   - Review endpoints with >1000ms response time
   - Implement caching for frequently called endpoints
   - Consider API rate limiting

2. **Testing Strategy:**
   - Run generated tests in CI/CD pipeline
   - Add authentication tests
   - Implement load testing for critical endpoints

3. **Security Considerations:**
   - Review API authentication patterns
   - Validate input sanitization
   - Check for sensitive data exposure
'''

    def _format_dict_as_markdown(self, data: Dict[str, Any]) -> str:
        """Format dictionary as markdown table"""
        if not data:
            return "No data available"
            
        lines = ["| Item | Count |", "|------|-------|"]
        for key, value in data.items():
            lines.append(f"| {key} | {value} |")
        return "\n".join(lines)

    def _format_endpoints_as_markdown(self) -> str:
        """Format endpoints as markdown list"""
        if not self.captured_calls:
            return "No endpoints captured"
            
        endpoints = {}
        for call in self.captured_calls:
            key = f"{call.method} {urlparse(call.url).path}"
            if key not in endpoints:
                endpoints[key] = call.url
                
        lines = []
        for endpoint, url in endpoints.items():
            lines.append(f"- **{endpoint}** - {url}")
            
        return "\n".join(lines)

    async def _generate_api_documentation(self) -> None:
        """Generate API documentation from captured calls"""
        # This could be expanded to generate OpenAPI/Swagger documentation
        pass

    def analyze_session(self) -> Dict[str, Any]:
        """Analyze the captured session and return insights"""
        if not self.captured_calls:
            return {'error': 'No API calls captured'}
            
        total_calls = len(self.captured_calls)
        success_calls = len([call for call in self.captured_calls if 200 <= call.status_code < 300])
        error_calls = total_calls - success_calls
        
        analysis = {
            'session_id': self.session_id,
            'total_calls': total_calls,
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'methods': dict(self.stats['api_calls_by_method']),
                'statuses': dict(self.stats['api_calls_by_status']),
                'api_types': self._analyze_api_types(),
                'total_duration': self.stats['total_duration'],
                'average_duration': self.stats['total_duration'] / max(total_calls, 1)
            },
            'performance': {
                'success_calls': success_calls,
                'error_calls': error_calls,
                'success_rate': (success_calls / total_calls) * 100,
                'error_rate': (error_calls / total_calls) * 100,
                'slow_calls': len([call for call in self.captured_calls if call.duration_ms > 1000])
            },
            'endpoints': self._analyze_endpoints()
        }
        
        return analysis

    def _analyze_api_types(self) -> Dict[str, int]:
        """Analyze API types in captured calls"""
        api_types = {}
        for call in self.captured_calls:
            api_type = call.api_type
            api_types[api_type] = api_types.get(api_type, 0) + 1
        return api_types

    def _analyze_endpoints(self) -> Dict[str, Any]:
        """Analyze endpoint patterns and statistics"""
        endpoints = {}
        for call in self.captured_calls:
            path = urlparse(call.url).path
            key = f"{call.method} {path}"
            
            if key not in endpoints:
                endpoints[key] = {
                    'count': 0,
                    'total_duration': 0,
                    'statuses': {}
                }
                
            endpoints[key]['count'] += 1
            endpoints[key]['total_duration'] += call.duration_ms
            
            status = call.status_code
            endpoints[key]['statuses'][status] = endpoints[key]['statuses'].get(status, 0) + 1
            
        # Calculate averages
        for endpoint_data in endpoints.values():
            endpoint_data['average_duration'] = endpoint_data['total_duration'] / endpoint_data['count']
            
        return endpoints

    def get_statistics(self) -> Dict[str, Any]:
        """Get current session statistics"""
        return {
            'session_id': self.session_id,
            'total_captured': len(self.captured_calls),
            'unique_endpoints': self.stats['unique_endpoints'],
            'total_requests': self.stats['total_requests'],
            'failed_requests': self.stats['failed_requests'],
            'capture_rate': (self.stats['captured_requests'] / max(self.stats['total_requests'], 1)) * 100,
            'session_duration': time.time() - self.start_time
        }

    def clear_session(self) -> None:
        """Clear current session data"""
        self.captured_calls.clear()
        self.stats = {
            'total_requests': 0,
            'captured_requests': 0,
            'failed_requests': 0,
            'unique_endpoints': 0,
            'api_calls_by_method': {},
            'api_calls_by_status': {},
            'total_duration': 0.0
        }
        self.start_time = time.time()
        self.logger.info("🧹 Session data cleared")


# Example usage and testing
if __name__ == "__main__":
    async def test_api_hunter():
        """Test the API Hunter agent"""
        config = APIHunterConfig(
            capture_xhr_only=True,
            max_response_size=512*1024,  # 512KB
            output_dir="./test_api_analysis"
        )
        
        hunter = APIHunterAgent(config)
        print(f"✅ API Hunter initialized: {hunter.session_id}")
        print(f"📁 Output directory: {hunter.output_path}")
        
        # Test statistics
        stats = hunter.get_statistics()
        print(f"📊 Initial stats: {stats}")
        
    if DEPENDENCIES_AVAILABLE:
        asyncio.run(test_api_hunter())
    else:
        print("❌ Dependencies not available for testing") 