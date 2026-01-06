"""System status check task"""

import subprocess
import psutil
from pathlib import Path
from typing import Dict, Any

from src.utils.markdown import MarkdownReport
from src.utils.shell import ShellRunner


class SystemStatusTask:
    """Check system status (nginx, php-fpm, mariadb, disk, ram)"""
    
    def __init__(self, config: dict):
        self.config = config
        self.shell = ShellRunner(timeout=30)
    
    def execute(
        self,
        job_id: str,
        workspace_dir: str,
        logs_path: str,
        report_path: str,
    ) -> Dict[str, Any]:
        """Execute system status check"""
        report = MarkdownReport("Server Status Report")
        
        # Check services
        services_status = self._check_services()
        report.add_checked_item("System services (nginx, php-fpm, mariadb)")
        
        # Check disk usage
        disk_status = self._check_disk()
        report.add_checked_item("Disk usage")
        
        # Check memory
        memory_status = self._check_memory()
        report.add_checked_item("Memory usage")
        
        # Check CPU
        cpu_status = self._check_cpu()
        report.add_checked_item("CPU usage")
        
        # Determine overall status
        overall_status = "green"
        if any(s.get('status') != 'running' for s in services_status.values()):
            overall_status = "red"
        elif disk_status.get('usage_percent', 0) > 90 or memory_status.get('usage_percent', 0) > 90:
            overall_status = "yellow"
        
        # Build summary
        summary_lines = []
        summary_lines.append(f"**Services:** {sum(1 for s in services_status.values() if s['status'] == 'running')}/{len(services_status)} running")
        summary_lines.append(f"**Disk:** {disk_status.get('usage_percent', 0):.1f}% used ({disk_status.get('free_gb', 0):.1f} GB free)")
        summary_lines.append(f"**Memory:** {memory_status.get('usage_percent', 0):.1f}% used ({memory_status.get('free_gb', 0):.1f} GB free)")
        summary_lines.append(f"**CPU:** {cpu_status.get('usage_percent', 0):.1f}%")
        
        report.set_summary(overall_status, "\n".join(summary_lines))
        
        # Add findings
        for service_name, service_info in services_status.items():
            if service_info['status'] == 'running':
                report.add_finding(
                    'good',
                    f"{service_name} is running",
                    f"PID: {service_info.get('pid', 'N/A')}"
                )
            else:
                report.add_finding(
                    'critical',
                    f"{service_name} is not running",
                    f"Service status: {service_info.get('status', 'unknown')}",
                    f"Start service: sudo systemctl start {service_name}"
                )
        
        if disk_status.get('usage_percent', 0) > 90:
            report.add_finding(
                'critical',
                "Disk usage is critical",
                f"Disk is {disk_status.get('usage_percent', 0):.1f}% full",
                "Free up disk space or expand storage"
            )
        elif disk_status.get('usage_percent', 0) > 80:
            report.add_finding(
                'warning',
                "Disk usage is high",
                f"Disk is {disk_status.get('usage_percent', 0):.1f}% full",
                "Consider cleaning up old files"
            )
        
        if memory_status.get('usage_percent', 0) > 90:
            report.add_finding(
                'warning',
                "Memory usage is high",
                f"Memory is {memory_status.get('usage_percent', 0):.1f}% used",
                "Monitor memory usage and consider adding more RAM"
            )
        
        # Save report
        report.save(report_path)
        
        return {
            'status': overall_status,
            'services': services_status,
            'disk': disk_status,
            'memory': memory_status,
            'cpu': cpu_status,
        }
    
    def _check_services(self) -> Dict[str, Dict[str, Any]]:
        """Check system services"""
        services = {}
        service_names = ['nginx', 'php8.3-fpm', 'mariadb']
        
        for service_name in service_names:
            try:
                result = subprocess.run(
                    ['systemctl', 'is-active', service_name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                is_active = result.stdout.strip() == 'active'
                
                if is_active:
                    # Get PID
                    try:
                        result = subprocess.run(
                            ['systemctl', 'show', service_name, '--property=MainPID', '--value'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        pid = result.stdout.strip()
                        pid = int(pid) if pid.isdigit() else None
                    except:
                        pid = None
                    
                    services[service_name] = {
                        'status': 'running',
                        'pid': pid
                    }
                else:
                    services[service_name] = {
                        'status': 'stopped'
                    }
            except Exception as e:
                services[service_name] = {
                    'status': 'unknown',
                    'error': str(e)
                }
        
        return services
    
    def _check_disk(self) -> Dict[str, Any]:
        """Check disk usage"""
        try:
            disk = psutil.disk_usage('/')
            total_gb = disk.total / (1024 ** 3)
            used_gb = disk.used / (1024 ** 3)
            free_gb = disk.free / (1024 ** 3)
            usage_percent = (disk.used / disk.total) * 100
            
            return {
                'total_gb': total_gb,
                'used_gb': used_gb,
                'free_gb': free_gb,
                'usage_percent': usage_percent
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _check_memory(self) -> Dict[str, Any]:
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            total_gb = memory.total / (1024 ** 3)
            used_gb = memory.used / (1024 ** 3)
            free_gb = memory.available / (1024 ** 3)
            usage_percent = memory.percent
            
            return {
                'total_gb': total_gb,
                'used_gb': used_gb,
                'free_gb': free_gb,
                'usage_percent': usage_percent
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _check_cpu(self) -> Dict[str, Any]:
        """Check CPU usage"""
        try:
            usage_percent = psutil.cpu_percent(interval=1)
            count = psutil.cpu_count()
            
            return {
                'usage_percent': usage_percent,
                'cores': count
            }
        except Exception as e:
            return {'error': str(e)}

