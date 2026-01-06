"""Public site security audit task"""

import requests
from urllib.parse import urljoin
from typing import Dict, Any, List
import ssl
import socket

from src.utils.markdown import MarkdownReport
from src.utils.config import load_config


class AuditPublicSiteTask:
    """Audit publicly accessible endpoints"""
    
    def __init__(self, config: dict):
        self.config = config
        self.target_domain = config.get('audit', {}).get('target_domain', 'https://jaysonkhan.com')
        self.timeout = config.get('audit', {}).get('request_timeout', 10)
        self.user_agent = config.get('audit', {}).get('user_agent', 'AutoBuilder-Bot/1.0')
    
    def execute(
        self,
        job_id: str,
        workspace_dir: str,
        logs_path: str,
        report_path: str,
    ) -> Dict[str, Any]:
        """Execute security audit"""
        report = MarkdownReport("Security Audit Report")
        
        findings = []
        
        # Check common exposed files/directories
        exposed_paths = self._check_exposed_paths()
        findings.extend(exposed_paths)
        report.add_checked_item("Common exposed paths (.env, .git, backup files)")
        
        # Check TLS/SSL
        tls_info = self._check_tls()
        findings.extend(tls_info)
        report.add_checked_item("TLS/SSL configuration")
        
        # Check HTTP headers
        headers_info = self._check_headers()
        findings.extend(headers_info)
        report.add_checked_item("HTTP security headers")
        
        # Check .well-known/assetlinks.json
        assetlinks_info = self._check_assetlinks()
        findings.extend(assetlinks_info)
        report.add_checked_item(".well-known/assetlinks.json")
        
        # Determine overall status
        critical_count = sum(1 for f in findings if f.get('severity') == 'critical')
        warning_count = sum(1 for f in findings if f.get('severity') == 'warning')
        
        if critical_count > 0:
            overall_status = "red"
        elif warning_count > 0:
            overall_status = "yellow"
        else:
            overall_status = "green"
        
        summary = f"""
**Target:** {self.target_domain}
**Critical Issues:** {critical_count}
**Warnings:** {warning_count}
**Total Checks:** {len(findings)}
"""
        report.set_summary(overall_status, summary)
        
        # Add findings to report
        for finding in findings:
            report.add_finding(
                finding.get('severity', 'info'),
                finding.get('title', ''),
                finding.get('description', ''),
                finding.get('recommendation')
            )
        
        # Save report
        report.save(report_path)
        
        return {
            'status': overall_status,
            'findings_count': len(findings),
            'critical_count': critical_count,
            'warning_count': warning_count,
        }
    
    def _check_exposed_paths(self) -> List[Dict[str, Any]]:
        """Check for common exposed files/directories"""
        findings = []
        paths_to_check = [
            '/.env',
            '/.git',
            '/backup.zip',
            '/backup.sql',
            '/phpinfo.php',
            '/.htaccess',
            '/wp-config.php',
            '/config.php',
            '/.env.local',
            '/.env.production',
        ]
        
        for path in paths_to_check:
            url = urljoin(self.target_domain, path)
            try:
                response = requests.head(
                    url,
                    timeout=self.timeout,
                    allow_redirects=False,
                    headers={'User-Agent': self.user_agent}
                )
                
                if response.status_code == 200:
                    findings.append({
                        'severity': 'critical',
                        'title': f"Exposed path found: {path}",
                        'description': f"Path {path} is publicly accessible (HTTP {response.status_code})",
                        'recommendation': f"Remove or restrict access to {path}. Use .htaccess or Nginx rules to block access."
                    })
                elif response.status_code in [301, 302, 303, 307, 308]:
                    findings.append({
                        'severity': 'warning',
                        'title': f"Redirect found: {path}",
                        'description': f"Path {path} redirects (HTTP {response.status_code})",
                        'recommendation': f"Verify that {path} is not exposing sensitive information."
                    })
            except requests.exceptions.RequestException:
                # Path not accessible or doesn't exist - this is good
                pass
        
        return findings
    
    def _check_tls(self) -> List[Dict[str, Any]]:
        """Check TLS/SSL configuration"""
        findings = []
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(self.target_domain)
            hostname = parsed.hostname
            port = parsed.port or 443
            
            # Create SSL context
            context = ssl.create_default_context()
            
            with socket.create_connection((hostname, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    version = ssock.version()
                    
                    # Check TLS version
                    if version in ['TLSv1', 'TLSv1.1']:
                        findings.append({
                            'severity': 'critical',
                            'title': f"Outdated TLS version: {version}",
                            'description': f"Server uses {version}, which is deprecated and insecure",
                            'recommendation': "Upgrade to TLS 1.2 or higher in Nginx configuration"
                        })
                    elif version in ['TLSv1.2', 'TLSv1.3']:
                        findings.append({
                            'severity': 'good',
                            'title': f"TLS version is secure: {version}",
                            'description': f"Server uses {version}",
                        })
        except Exception as e:
            findings.append({
                'severity': 'warning',
                'title': "Could not verify TLS configuration",
                'description': f"Error: {str(e)}",
            })
        
        return findings
    
    def _check_headers(self) -> List[Dict[str, Any]]:
        """Check HTTP security headers"""
        findings = []
        
        try:
            response = requests.get(
                self.target_domain,
                timeout=self.timeout,
                headers={'User-Agent': self.user_agent},
                allow_redirects=True
            )
            
            headers = response.headers
            
            # Check HSTS
            if 'Strict-Transport-Security' not in headers:
                findings.append({
                    'severity': 'warning',
                    'title': "HSTS header missing",
                    'description': "Strict-Transport-Security header is not set",
                    'recommendation': "Add 'add_header Strict-Transport-Security \"max-age=31536000; includeSubDomains\" always;' to Nginx config"
                })
            
            # Check X-Content-Type-Options
            if 'X-Content-Type-Options' not in headers:
                findings.append({
                    'severity': 'warning',
                    'title': "X-Content-Type-Options header missing",
                    'description': "X-Content-Type-Options header is not set",
                    'recommendation': "Add 'add_header X-Content-Type-Options \"nosniff\" always;' to Nginx config"
                })
            
            # Check X-Frame-Options
            if 'X-Frame-Options' not in headers:
                findings.append({
                    'severity': 'info',
                    'title': "X-Frame-Options header missing",
                    'description': "X-Frame-Options header is not set",
                    'recommendation': "Add 'add_header X-Frame-Options \"SAMEORIGIN\" always;' to Nginx config"
                })
            
            # Check Content-Security-Policy
            if 'Content-Security-Policy' not in headers:
                findings.append({
                    'severity': 'info',
                    'title': "Content-Security-Policy header missing",
                    'description': "Content-Security-Policy header is not set",
                    'recommendation': "Consider adding Content-Security-Policy header for additional security"
                })
            
        except Exception as e:
            findings.append({
                'severity': 'warning',
                'title': "Could not check HTTP headers",
                'description': f"Error: {str(e)}",
            })
        
        return findings
    
    def _check_assetlinks(self) -> List[Dict[str, Any]]:
        """Check .well-known/assetlinks.json"""
        findings = []
        
        url = urljoin(self.target_domain, '/.well-known/assetlinks.json')
        try:
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={'User-Agent': self.user_agent}
            )
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    findings.append({
                        'severity': 'good',
                        'title': ".well-known/assetlinks.json is properly configured",
                        'description': f"File exists and has correct Content-Type: {content_type}",
                    })
                else:
                    findings.append({
                        'severity': 'warning',
                        'title': ".well-known/assetlinks.json has incorrect Content-Type",
                        'description': f"Content-Type is {content_type}, should be application/json",
                        'recommendation': "Set correct Content-Type in Nginx: 'add_header Content-Type application/json;'"
                    })
        except requests.exceptions.RequestException:
            # File doesn't exist - this is fine, not required
            pass
        
        return findings

