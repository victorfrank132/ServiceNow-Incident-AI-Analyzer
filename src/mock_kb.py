"""Mock knowledge base for incident analysis."""

from typing import List, Dict, Any


class MockKnowledgeBase:
    """Mock knowledge base containing sample incidents and resolutions."""

    def __init__(self):
        """Initialize mock knowledge base with sample incidents."""
        self.incidents = [
            {
                "id": "KB001",
                "title": "Database Connection Timeout",
                "description": "Applications unable to connect to database due to connection pool exhaustion",
                "category": "Database",
                "root_cause": "Too many open connections from application servers",
                "resolution_steps": [
                    "Check active connections in database",
                    "Review application connection pool settings",
                    "Restart database connection service if necessary",
                    "Increase connection pool size if persistent"
                ],
                "keywords": ["database", "connection", "timeout", "pool", "oracle", "mysql"],
                "assignment_group": "Database"
            },
            {
                "id": "KB002",
                "title": "High CPU Usage on Server",
                "description": "Server experiencing sustained high CPU utilization above 90%",
                "category": "Infrastructure",
                "root_cause": "Runaway process or inefficient code execution",
                "resolution_steps": [
                    "Identify top CPU consuming processes",
                    "Check for memory leaks using top/htop",
                    "Review application logs for errors",
                    "Consider process restart or code optimization"
                ],
                "keywords": ["cpu", "high", "usage", "process", "server", "load"],
                "assignment_group": "Infrastructure"
            },
            {
                "id": "KB003",
                "title": "Network Connectivity Loss",
                "description": "Users unable to reach external services or internet",
                "category": "Networking",
                "root_cause": "Network interface failure, routing issue, or firewall misconfiguration",
                "resolution_steps": [
                    "Verify network interface status",
                    "Check firewall rules and policies",
                    "Test network connectivity with ping/traceroute",
                    "Review router and gateway configurations"
                ],
                "keywords": ["network", "connectivity", "internet", "firewall", "routing", "link"],
                "assignment_group": "Networking"
            },
            {
                "id": "KB004",
                "title": "Application Crashes on Startup",
                "description": "Application fails to start with error in logs",
                "category": "Application",
                "root_cause": "Missing configuration, corrupted files, or dependency issues",
                "resolution_steps": [
                    "Review application error logs",
                    "Verify configuration files are present",
                    "Check file permissions and ownership",
                    "Verify dependencies are installed"
                ],
                "keywords": ["application", "crash", "startup", "error", "fail", "load"],
                "assignment_group": "Application"
            },
            {
                "id": "KB005",
                "title": "Disk Space Critical",
                "description": "Server disk usage at 95% or above capacity",
                "category": "Infrastructure",
                "root_cause": "Log file growth, temporary files, or increased data",
                "resolution_steps": [
                    "Identify large directories and files",
                    "Archive or delete old log files",
                    "Clean temporary directories",
                    "Monitor disk usage trends"
                ],
                "keywords": ["disk", "space", "storage", "full", "capacity", "drive"],
                "assignment_group": "Infrastructure"
            },
            {
                "id": "KB006",
                "title": "Email Delivery Failure",
                "description": "Emails not being delivered to recipients",
                "category": "Email",
                "root_cause": "SMTP server issue, mail queue full, or DNS/MX record problem",
                "resolution_steps": [
                    "Check SMTP server status",
                    "Verify mail queue for stuck messages",
                    "Test email connectivity",
                    "Verify DNS MX records"
                ],
                "keywords": ["email", "mail", "delivery", "smtp", "queue", "send"],
                "assignment_group": "Email"
            },
            {
                "id": "KB007",
                "title": "VPN Connection Refused",
                "description": "Users unable to establish VPN connection",
                "category": "VPN",
                "root_cause": "VPN server down, authentication issue, or client configuration",
                "resolution_steps": [
                    "Verify VPN server is running",
                    "Check authentication services",
                    "Review client VPN configuration",
                    "Verify user VPN credentials and permissions"
                ],
                "keywords": ["vpn", "connection", "refused", "tunnel", "access", "remote"],
                "assignment_group": "Networking"
            },
            {
                "id": "KB008",
                "title": "Backup Job Failure",
                "description": "Daily backup job failed with error status",
                "category": "Backup",
                "root_cause": "Storage full, network connectivity, or backup service issue",
                "resolution_steps": [
                    "Verify backup storage capacity",
                    "Check network connectivity to backup target",
                    "Review backup job logs for error details",
                    "Restart backup service if needed"
                ],
                "keywords": ["backup", "job", "failure", "restore", "storage", "archive"],
                "assignment_group": "Backup"
            },
            {
                "id": "KB009",
                "title": "SSL Certificate Expiration",
                "description": "SSL/TLS certificate expiring or expired on web server",
                "category": "Security",
                "root_cause": "Certificate renewal process was not completed",
                "resolution_steps": [
                    "Check current SSL certificate expiration date",
                    "Request new SSL certificate from CA",
                    "Install new certificate on server",
                    "Test HTTPS connectivity"
                ],
                "keywords": ["ssl", "certificate", "expiration", "https", "tls", "security"],
                "assignment_group": "Security"
            },
            {
                "id": "KB010",
                "title": "Memory Leak in Service",
                "description": "Service consuming increasing amounts of memory over time",
                "category": "Application",
                "root_cause": "Improper resource cleanup in application code",
                "resolution_steps": [
                    "Monitor memory usage with top/htop",
                    "Review application logs for resource warnings",
                    "Check for database connection leaks",
                    "Consider service restart or code review"
                ],
                "keywords": ["memory", "leak", "consume", "ram", "heap", "service"],
                "assignment_group": "Application"
            }
        ]

    def find_similar_incidents(self, description: str, title: str = "", limit: int = 3) -> List[Dict[str, Any]]:
        """
        Find similar incidents from the knowledge base using keyword matching.

        Args:
            description: Incident description text
            title: Incident title (optional)
            limit: Maximum number of similar incidents to return

        Returns:
            List of similar incident dictionaries
        """
        search_text = f"{title} {description}".lower()
        scored_incidents = []

        for incident in self.incidents:
            score = 0
            # Check for keyword matches
            for keyword in incident["keywords"]:
                if keyword in search_text:
                    score += 1

            # Check for title/category matching
            if incident["category"].lower() in search_text:
                score += 2

            if score > 0:
                scored_incidents.append((score, incident))

        # Sort by score and return top matches
        scored_incidents.sort(key=lambda x: x[0], reverse=True)
        return [incident for score, incident in scored_incidents[:limit]]

    def get_all_categories(self) -> List[str]:
        """Get list of all categories in knowledge base."""
        categories = set()
        for incident in self.incidents:
            categories.add(incident["category"])
        return sorted(list(categories))

    def get_incidents_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all incidents for a specific category."""
        return [incident for incident in self.incidents if incident["category"] == category]
