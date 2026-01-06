"""Load test task (DDoS simulation)"""

import asyncio
import aiohttp
import time
from typing import Dict, Any
from urllib.parse import urlparse

from src.utils.markdown import MarkdownReport


class LoadTestTask:
    """Perform load test on a target (only allowed domains)"""
    
    # Allowed domains (only test your own servers)
    ALLOWED_DOMAINS = [
        'jaysonkhan.com',
        'localhost',
        '127.0.0.1',
    ]
    
    def __init__(self, config: dict, target_url: str, request_count: int):
        self.config = config
        self.target_url = target_url
        self.request_count = min(request_count, 10000)  # Max 10000 requests
        self.timeout = 10
    
    def execute(
        self,
        job_id: str,
        workspace_dir: str,
        logs_path: str,
        report_path: str,
    ) -> Dict[str, Any]:
        """Execute load test"""
        report = MarkdownReport(f"Load Test Report: {self.target_url}")
        
        # Parse URL
        parsed = urlparse(self.target_url if '://' in self.target_url else f"http://{self.target_url}")
        hostname = parsed.hostname or self.target_url
        
        # Security check - only allow specific domains
        if not self._is_allowed(hostname):
            report.set_summary("red", f"❌ Security: {hostname} is not in allowed domains list")
            report.add_finding(
                'critical',
                "Domain not allowed",
                f"Load testing is only allowed for: {', '.join(self.ALLOWED_DOMAINS)}",
                "Add domain to ALLOWED_DOMAINS list if it's your server"
            )
            report.save(report_path)
            raise ValueError(f"Domain {hostname} is not allowed for load testing")
        
        # Run load test
        report.add_checked_item(f"Load test: {self.request_count} requests to {self.target_url}")
        
        results = asyncio.run(self._run_load_test())
        
        # Build summary
        success_rate = (results['successful'] / results['total']) * 100 if results['total'] > 0 else 0
        avg_time = results['total_time'] / results['successful'] if results['successful'] > 0 else 0
        
        overall_status = "green" if success_rate > 95 else "yellow" if success_rate > 80 else "red"
        
        summary_lines = []
        summary_lines.append(f"**Target:** {self.target_url}")
        summary_lines.append(f"**Total Requests:** {results['total']}")
        summary_lines.append(f"**Successful:** {results['successful']} ({success_rate:.1f}%)")
        summary_lines.append(f"**Failed:** {results['failed']}")
        summary_lines.append(f"**Average Response Time:** {avg_time:.2f}ms")
        summary_lines.append(f"**Total Time:** {results['total_time']:.2f}s")
        summary_lines.append(f"**Requests/Second:** {results['total'] / results['total_time']:.2f}" if results['total_time'] > 0 else "**Requests/Second:** N/A")
        
        report.set_summary(overall_status, "\n".join(summary_lines))
        
        # Add findings
        report.add_finding(
            'info',
            f"Load test completed",
            f"{results['successful']}/{results['total']} requests successful"
        )
        
        if results['failed'] > 0:
            report.add_finding(
                'warning',
                f"{results['failed']} requests failed",
                "Server may be overloaded or experiencing issues"
            )
        
        report.add_finding(
            'info',
            f"Performance metrics",
            f"Average response time: {avg_time:.2f}ms, Throughput: {results['total'] / results['total_time']:.2f} req/s" if results['total_time'] > 0 else "N/A"
        )
        
        # Save report
        report.save(report_path)
        
        return results
    
    def _is_allowed(self, hostname: str) -> bool:
        """Check if hostname is in allowed list"""
        # Check exact match
        if hostname in self.ALLOWED_DOMAINS:
            return True
        
        # Check subdomain
        for allowed in self.ALLOWED_DOMAINS:
            if hostname.endswith(f".{allowed}"):
                return True
        
        return False
    
    async def _run_load_test(self) -> Dict[str, Any]:
        """Run async load test"""
        url = self.target_url if '://' in self.target_url else f"http://{self.target_url}"
        
        successful = 0
        failed = 0
        start_time = time.time()
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            tasks = []
            for i in range(self.request_count):
                task = self._make_request(session, url)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    failed += 1
                elif result:
                    successful += 1
                else:
                    failed += 1
        
        total_time = time.time() - start_time
        
        return {
            'total': self.request_count,
            'successful': successful,
            'failed': failed,
            'total_time': total_time
        }
    
    async def _make_request(self, session: aiohttp.ClientSession, url: str) -> bool:
        """Make a single request"""
        try:
            async with session.get(url) as response:
                return response.status < 500
        except:
            return False

