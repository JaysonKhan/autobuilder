"""Remote server status check task"""

import subprocess
import requests
from typing import Dict, Any
import socket
from urllib.parse import urlparse

from src.utils.markdown import MarkdownReport
from src.utils.shell import ShellRunner


class RemoteStatusTask:
    """Check remote server status"""
    
    def __init__(self, config: dict, target_host: str):
        self.config = config
        self.target_host = target_host
        self.shell = ShellRunner(timeout=30)
    
    def execute(
        self,
        job_id: str,
        workspace_dir: str,
        logs_path: str,
        report_path: str,
    ) -> Dict[str, Any]:
        """Execute remote status check"""
        report = MarkdownReport(f"Remote Server Status: {self.target_host}")
        
        # Parse host
        parsed = urlparse(self.target_host if '://' in self.target_host else f"http://{self.target_host}")
        hostname = parsed.hostname or self.target_host
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        
        # Check DNS resolution
        dns_status = self._check_dns(hostname)
        report.add_checked_item(f"DNS resolution for {hostname}")
        
        # Check HTTP/HTTPS response
        http_status = self._check_http(hostname, port, parsed.scheme or 'http')
        report.add_checked_item(f"HTTP/HTTPS response")
        
        # Check ping
        ping_status = self._check_ping(hostname)
        report.add_checked_item(f"Ping connectivity")
        
        # Check ports
        ports_status = self._check_ports(hostname)
        report.add_checked_item(f"Common ports")
        
        # Determine overall status
        overall_status = "green"
        if not dns_status.get('resolved'):
            overall_status = "red"
        elif not http_status.get('accessible'):
            overall_status = "yellow"
        
        # Build summary
        summary_lines = []
        summary_lines.append(f"**Target:** {self.target_host}")
        summary_lines.append(f"**DNS:** {'✅ Resolved' if dns_status.get('resolved') else '❌ Failed'}")
        summary_lines.append(f"**HTTP:** {'✅ Accessible' if http_status.get('accessible') else '❌ Not accessible'}")
        summary_lines.append(f"**Ping:** {'✅ OK' if ping_status.get('success') else '❌ Failed'}")
        summary_lines.append(f"**Response Time:** {http_status.get('response_time', 'N/A')}ms")
        
        report.set_summary(overall_status, "\n".join(summary_lines))
        
        # Add findings
        if dns_status.get('resolved'):
            report.add_finding(
                'good',
                f"DNS resolution successful",
                f"IP: {dns_status.get('ip', 'N/A')}"
            )
        else:
            report.add_finding(
                'critical',
                f"DNS resolution failed",
                f"Could not resolve {hostname}",
                "Check DNS configuration"
            )
        
        if http_status.get('accessible'):
            report.add_finding(
                'good',
                f"HTTP/HTTPS accessible",
                f"Status: {http_status.get('status_code', 'N/A')}, Response time: {http_status.get('response_time', 'N/A')}ms"
            )
        else:
            report.add_finding(
                'warning',
                f"HTTP/HTTPS not accessible",
                http_status.get('error', 'Unknown error')
            )
        
        if ping_status.get('success'):
            report.add_finding(
                'good',
                f"Ping successful",
                f"Average: {ping_status.get('avg_time', 'N/A')}ms"
            )
        
        # Save report
        report.save(report_path)
        
        return {
            'status': overall_status,
            'dns': dns_status,
            'http': http_status,
            'ping': ping_status,
        }
    
    def _check_dns(self, hostname: str) -> Dict[str, Any]:
        """Check DNS resolution"""
        try:
            ip = socket.gethostbyname(hostname)
            return {'resolved': True, 'ip': ip}
        except socket.gaierror:
            return {'resolved': False, 'error': 'DNS resolution failed'}
    
    def _check_http(self, hostname: str, port: int, scheme: str) -> Dict[str, Any]:
        """Check HTTP/HTTPS response"""
        try:
            url = f"{scheme}://{hostname}:{port}" if port not in [80, 443] else f"{scheme}://{hostname}"
            import time
            start = time.time()
            response = requests.get(url, timeout=10, allow_redirects=True)
            response_time = int((time.time() - start) * 1000)
            
            return {
                'accessible': True,
                'status_code': response.status_code,
                'response_time': response_time,
                'headers': dict(response.headers)
            }
        except Exception as e:
            return {
                'accessible': False,
                'error': str(e)
            }
    
    def _check_ping(self, hostname: str) -> Dict[str, Any]:
        """Check ping"""
        try:
            result = subprocess.run(
                ['ping', '-c', '4', hostname],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse avg time
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'avg' in line.lower() or 'average' in line.lower():
                        # Extract time
                        import re
                        times = re.findall(r'(\d+\.?\d*)\s*ms', line)
                        if times:
                            avg_time = sum(float(t) for t in times) / len(times)
                            return {'success': True, 'avg_time': f"{avg_time:.2f}"}
                
                return {'success': True, 'avg_time': 'N/A'}
            else:
                return {'success': False, 'error': result.stderr}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _check_ports(self, hostname: str) -> Dict[str, Any]:
        """Check common ports"""
        common_ports = [22, 80, 443, 3306, 5432]
        results = {}
        
        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((hostname, port))
                sock.close()
                results[port] = result == 0
            except:
                results[port] = False
        
        return results

