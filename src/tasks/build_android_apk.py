"""Build Android APK task"""

import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

from src.utils.markdown import MarkdownReport
from src.utils.shell import ShellRunner
from src.tasks.github_push import GitHubPusher


class BuildWeatherApkTask:
    """Build a weather app APK"""
    
    def __init__(self, config: dict):
        self.config = config
        self.shell = ShellRunner(timeout=1800)  # 30 minutes
        self.flutter_path = config.get('build', {}).get('flutter_path', 'flutter')
        self.github_pusher = GitHubPusher(config)
    
    def execute(
        self,
        job_id: str,
        workspace_dir: str,
        logs_path: str,
        report_path: str,
        city: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute build task"""
        report = MarkdownReport("Weather App Build Report")
        
        city = city or "Tashkent"
        language = language or "en"
        
        app_dir = Path(workspace_dir) / "app"
        
        try:
            # Step 1: Create Flutter project
            report.add_checked_item("Create Flutter project")
            self._create_flutter_project(app_dir)
            
            # Step 2: Generate weather app code
            report.add_checked_item("Generate weather app code")
            self._generate_weather_app_code(app_dir, city, language)
            
            # Step 3: Build APK
            report.add_checked_item("Build Android APK")
            apk_path = self._build_apk(app_dir)
            
            # Step 4: Push to GitHub
            report.add_checked_item("Push code to GitHub")
            github_result = self.github_pusher.push_changes(
                str(app_dir),
                job_id,
                f"[{job_id}] Weather app - {city}"
            )
            
            if github_result['success']:
                report.add_finding(
                    'good',
                    "Code pushed to GitHub",
                    f"Successfully pushed to {self.config.get('github', {}).get('branch', 'myself')} branch"
                )
            else:
                report.add_finding(
                    'warning',
                    "GitHub push failed",
                    github_result['message']
                )
            
            # Build summary
            if apk_path and apk_path.exists():
                report.set_summary("green", f"✅ APK built successfully!\n\n**Location:** {apk_path}\n**City:** {city}\n**Language:** {language}")
                report.add_finding(
                    'good',
                    "APK build successful",
                    f"APK file created at {apk_path}"
                )
            else:
                report.set_summary("red", "❌ APK build failed")
                report.add_finding(
                    'critical',
                    "APK build failed",
                    "APK file was not created"
                )
            
            report.save(report_path)
            
            return {
                'success': apk_path and apk_path.exists(),
                'apk_path': str(apk_path) if apk_path else None,
                'github_pushed': github_result['success'],
            }
            
        except Exception as e:
            report.set_summary("red", f"❌ Build failed: {str(e)}")
            report.add_finding('critical', "Build error", str(e))
            report.save(report_path)
            raise
    
    def _create_flutter_project(self, app_dir: Path):
        """Create a new Flutter project"""
        app_dir.parent.mkdir(parents=True, exist_ok=True)
        
        success, output = self.shell.run_safe(
            f"{self.flutter_path} create --org com.autobuilder --project-name weather_app {app_dir}",
            timeout=300
        )
        
        if not success:
            raise Exception(f"Failed to create Flutter project: {output}")
    
    def _generate_weather_app_code(self, app_dir: Path, city: str, language: str):
        """Generate weather app code"""
        # Create a simple weather app
        main_dart = app_dir / "lib" / "main.dart"
        
        weather_app_code = f'''import 'package:flutter/material.dart';

void main() {{
  runApp(const WeatherApp());
}}

class WeatherApp extends StatelessWidget {{
  const WeatherApp({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return MaterialApp(
      title: 'Weather App',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const WeatherScreen(city: '{city}'),
    );
  }}
}}

class WeatherScreen extends StatefulWidget {{
  final String city;
  
  const WeatherScreen({{super.key, required this.city}});

  @override
  State<WeatherScreen> createState() => _WeatherScreenState();
}}

class _WeatherScreenState extends State<WeatherScreen> {{
  String _temperature = "25°C";
  String _condition = "Sunny";
  String _humidity = "60%";
  
  @override
  void initState() {{
    super.initState();
    _loadWeather();
  }}
  
  void _loadWeather() {{
    // Simulated weather data
    setState(() {{
      _temperature = "25°C";
      _condition = "Sunny";
      _humidity = "60%";
    }});
  }}
  
  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: Text('Weather - ${{widget.city}}'),
        backgroundColor: Colors.blue,
        foregroundColor: Colors.white,
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.wb_sunny,
              size: 100,
              color: Colors.orange,
            ),
            const SizedBox(height: 20),
            Text(
              _temperature,
              style: const TextStyle(
                fontSize: 48,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 10),
            Text(
              _condition,
              style: const TextStyle(
                fontSize: 24,
                color: Colors.grey,
              ),
            ),
            const SizedBox(height: 30),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _buildInfoCard('Humidity', _humidity),
                _buildInfoCard('Wind', '10 km/h'),
              ],
            ),
            const SizedBox(height: 30),
            ElevatedButton(
              onPressed: _loadWeather,
              child: const Text('Refresh'),
            ),
          ],
        ),
      ),
    );
  }}
  
  Widget _buildInfoCard(String label, String value) {{
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Text(
              label,
              style: const TextStyle(
                fontSize: 14,
                color: Colors.grey,
              ),
            ),
            const SizedBox(height: 5),
            Text(
              value,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }}
}}
'''
        
        main_dart.write_text(weather_app_code, encoding='utf-8')
    
    def _build_apk(self, app_dir: Path) -> Optional[Path]:
        """Build Android APK"""
        # Get dependencies
        success, output = self.shell.run_safe(
            f"cd {app_dir} && {self.flutter_path} pub get",
            timeout=300
        )
        
        if not success:
            raise Exception(f"Failed to get dependencies: {output}")
        
        # Build APK
        success, output = self.shell.run_safe(
            f"cd {app_dir} && {self.flutter_path} build apk --release",
            timeout=1200  # 20 minutes
        )
        
        if not success:
            raise Exception(f"Failed to build APK: {output}")
        
        # Find APK file
        apk_paths = [
            app_dir / "build" / "app" / "outputs" / "flutter-apk" / "app-release.apk",
            app_dir / "build" / "app" / "outputs" / "apk" / "release" / "app-release.apk",
        ]
        
        for apk_path in apk_paths:
            if apk_path.exists():
                return apk_path
        
        return None

