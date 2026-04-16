"""ServiceNow API client wrapper for incident management."""

import os
import sys
import logging
from typing import Dict, List, Any, Optional
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class ServiceNowClient:
    """Wrapper for ServiceNow REST API interactions."""

    def __init__(self, instance_url: str, username: str = None, password: str = None, 
                 client_id: str = None, client_secret: str = None, auth_type: str = "basic"):
        """
        Initialize ServiceNow client.

        Args:
            instance_url: ServiceNow instance URL (e.g., https://dev12345.service-now.com)
            username: Username for basic auth
            password: Password for basic auth
            client_id: OAuth client ID (for OAuth auth type)
            client_secret: OAuth client secret (for OAuth auth type)
            auth_type: "basic" or "oauth" authentication method
        """
        self.instance_url = instance_url.rstrip("/")
        self.username = username
        self.password = password
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_type = auth_type
        self.api_url = f"{self.instance_url}/api/now/v2"
        self.timeout = 30
        self.session = requests.Session()
        
        # Set up authentication
        if self.auth_type == "basic":
            self.session.auth = HTTPBasicAuth(self.username, self.password)
        logger.info(f"ServiceNow client initialized with {auth_type} authentication")

    def _get_headers(self) -> Dict[str, str]:
        """Return standard headers for API requests."""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _get_accept_headers(self) -> Dict[str, str]:
        """Return headers for non-JSON uploads/downloads."""
        return {
            "Accept": "application/json",
        }

    def get_new_incidents(self, state: List[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch new/open incidents from ServiceNow.

        Args:
            state: List of state values (1=New, 2=In Progress). Defaults to [1, 2]
            limit: Maximum number of incidents to fetch

        Returns:
            List of incident dictionaries
        """
        if state is None:
            state = ["1", "2"]  # New and In Progress

        try:
            # Build query using OR logic for state filters
            # Different ServiceNow instances use different query syntax
            state_query = "^OR".join([f"state={s}" for s in state])
            query_params = {
                "sysparm_query": f"{state_query}^ORDERBYDESCsys_created_on",
                "sysparm_limit": limit,
                "sysparm_fields": "sys_id,number,short_description,description,state,assigned_to,assignment_group,category,priority,urgency,impact"
            }

            response = self.session.get(
                f"{self.api_url}/table/incident",
                headers=self._get_headers(),
                params=query_params,
                timeout=self.timeout
            )

            if response.status_code == 200:
                incidents = response.json().get("result", [])
                logger.info(f"Fetched {len(incidents)} incidents from ServiceNow")
                return incidents
            else:
                logger.error(f"ServiceNow API error: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            logger.error(f"Error fetching incidents: {str(e)}")
            return []

    def get_incident_details(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific incident.

        Args:
            incident_id: ServiceNow incident sys_id or incident number

        Returns:
            Incident dictionary or None if not found
        """
        try:
            query = f"number={incident_id}" if incident_id.startswith("INC") else f"sys_id={incident_id}"

            response = self.session.get(
                f"{self.api_url}/table/incident",
                headers=self._get_headers(),
                params={"sysparm_query": query},
                timeout=self.timeout
            )

            if response.status_code == 200:
                results = response.json().get("result", [])
                return results[0] if results else None
            else:
                logger.error(f"Error fetching incident {incident_id}: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error getting incident details: {str(e)}")
            return None

    def add_comment_to_incident(self, incident_id: str, comment: str) -> bool:
        """
        Add a comment to an incident.

        Args:
            incident_id: ServiceNow incident sys_id
            comment: Comment text to add

        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {
                "comments": comment
            }

            response = self.session.patch(
                f"{self.api_url}/table/incident/{incident_id}",
                headers=self._get_headers(),
                json=update_data,
                timeout=self.timeout
            )

            if response.status_code == 200:
                logger.info(f"Added comment to incident {incident_id}")
                return True
            else:
                logger.error(f"Error adding comment to {incident_id}: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error adding comment: {str(e)}")
            return False

    def add_work_note_to_incident(self, incident_id: str, note: str) -> bool:
        """
        Add a work note to an incident.

        Args:
            incident_id: ServiceNow incident sys_id
            note: Work note text

        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.session.patch(
                f"{self.api_url}/table/incident/{incident_id}",
                headers=self._get_headers(),
                json={"work_notes": note},
                timeout=self.timeout
            )

            if response.status_code == 200:
                logger.info(f"Added work note to incident {incident_id}")
                return True

            logger.error(f"Error adding work note to {incident_id}: {response.status_code}")
            return False

        except Exception as e:
            logger.error(f"Error adding work note: {str(e)}")
            return False

    def upload_attachment_to_incident(
        self,
        incident_id: str,
        file_name: str,
        content: bytes,
        content_type: str = "text/plain",
    ) -> bool:
        """
        Upload an attachment to a ServiceNow incident.

        Args:
            incident_id: ServiceNow incident sys_id
            file_name: Name of the attachment file
            content: File bytes
            content_type: MIME type

        Returns:
            True if upload succeeds, False otherwise
        """
        try:
            response = self.session.post(
                f"{self.instance_url}/api/now/attachment/file",
                headers={
                    "Accept": "application/json",
                    "Content-Type": content_type,
                },
                params={
                    "table_name": "incident",
                    "table_sys_id": incident_id,
                    "file_name": file_name,
                },
                data=content,
                timeout=self.timeout,
            )

            if response.status_code in (200, 201):
                logger.info(f"Uploaded attachment {file_name} to incident {incident_id}")
                return True

            logger.error(f"Error uploading attachment to {incident_id}: {response.status_code} - {response.text}")
            return False

        except Exception as e:
            logger.error(f"Error uploading attachment: {str(e)}")
            return False

    def list_attachments_for_incident(self, incident_id: str) -> List[Dict[str, Any]]:
        """
        List attachments for a ServiceNow incident.

        Args:
            incident_id: ServiceNow incident sys_id

        Returns:
            List of attachment dictionaries
        """
        try:
            response = self.session.get(
                f"{self.instance_url}/api/now/attachment",
                headers=self._get_accept_headers(),
                params={
                    "table_name": "incident",
                    "table_sys_id": incident_id,
                    "sysparm_limit": 100,
                },
                timeout=self.timeout,
            )

            if response.status_code == 200:
                return response.json().get("result", [])

            logger.error(f"Error listing attachments for {incident_id}: {response.status_code}")
            return []

        except Exception as e:
            logger.error(f"Error listing attachments: {str(e)}")
            return []

    def update_assignment_group(self, incident_id: str, assignment_group: str) -> bool:
        """
        Reassign an incident to a specific assignment group.

        Args:
            incident_id: ServiceNow incident sys_id
            assignment_group: Assignment group name or sys_id

        Returns:
            True if successful, False otherwise
        """
        try:
            # Try to get assignment group ID
            group_id = self._get_assignment_group_id(assignment_group)
            if not group_id:
                logger.error(f"Assignment group '{assignment_group}' not found")
                return False

            update_data = {
                "assignment_group": group_id
            }

            response = self.session.patch(
                f"{self.api_url}/table/incident/{incident_id}",
                headers=self._get_headers(),
                json=update_data,
                timeout=self.timeout
            )

            if response.status_code == 200:
                logger.info(f"Reassigned incident {incident_id} to group {assignment_group}")
                return True
            else:
                logger.error(f"Error reassigning incident {incident_id}: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error updating assignment group: {str(e)}")
            return False

    def _get_assignment_group_id(self, group_name: str) -> Optional[str]:
        """
        Get sys_id of an assignment group by name.

        Args:
            group_name: Assignment group name

        Returns:
            sys_id of the group or None if not found
        """
        try:
            query_params = {
                "sysparm_query": f"name={group_name}",
                "sysparm_limit": 1,
                "sysparm_fields": "sys_id"
            }

            response = self.session.get(
                f"{self.api_url}/table/sys_user_group",
                headers=self._get_headers(),
                params=query_params,
                timeout=self.timeout
            )

            if response.status_code == 200:
                results = response.json().get("result", [])
                if results:
                    return results[0]["sys_id"]

            return None

        except Exception as e:
            logger.error(f"Error getting assignment group ID: {str(e)}")
            return None

    def get_system_property(self, property_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a ServiceNow system property by name.

        Args:
            property_name: Property name (for example x_my_scope.some_property)

        Returns:
            Property record or None if it does not exist
        """
        try:
            response = self.session.get(
                f"{self.api_url}/table/sys_properties",
                headers=self._get_headers(),
                params={
                    "sysparm_query": f"name={property_name}",
                    "sysparm_limit": 1,
                    "sysparm_fields": "sys_id,name,value,type,description"
                },
                timeout=self.timeout
            )

            if response.status_code == 200:
                results = response.json().get("result", [])
                return results[0] if results else None

            logger.error(
                f"Error fetching system property {property_name}: "
                f"{response.status_code} - {response.text}"
            )
            return None

        except Exception as e:
            logger.error(f"Error fetching system property {property_name}: {str(e)}")
            return None

    def set_system_property(
        self,
        property_name: str,
        value: str,
        description: str = None,
        property_type: str = "string",
    ) -> Optional[Dict[str, Any]]:
        """
        Create or update a ServiceNow system property.

        Args:
            property_name: Property name (for example x_my_scope.some_property)
            value: Property value
            description: Optional property description
            property_type: ServiceNow property type

        Returns:
            Updated/created property record or None if the request fails
        """
        try:
            existing_property = self.get_system_property(property_name)

            if existing_property:
                payload = {"value": value}
                if description is not None:
                    payload["description"] = description

                response = self.session.patch(
                    f"{self.api_url}/table/sys_properties/{existing_property['sys_id']}",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    logger.info(f"Updated system property {property_name}")
                    return response.json().get("result", {})

                logger.error(
                    f"Error updating system property {property_name}: "
                    f"{response.status_code} - {response.text}"
                )
                return None

            payload = {
                "name": property_name,
                "value": value,
                "type": property_type,
            }
            if description is not None:
                payload["description"] = description

            response = self.session.post(
                f"{self.api_url}/table/sys_properties",
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout
            )

            if response.status_code in (200, 201):
                logger.info(f"Created system property {property_name}")
                return response.json().get("result", {})

            logger.error(
                f"Error creating system property {property_name}: "
                f"{response.status_code} - {response.text}"
            )
            return None

        except Exception as e:
            logger.error(f"Error setting system property {property_name}: {str(e)}")
            return None

    def close_incident(self, incident_id: str, resolution_notes: str, close_reason: str = "Resolved Remotely") -> bool:
        """
        Close/resolve an incident.

        Args:
            incident_id: ServiceNow incident sys_id
            resolution_notes: Notes explaining the resolution
            close_reason: Reason for closure (e.g., "Resolved Remotely", "User Confirmed Resolution")

        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {
                "state": "6",  # 6 = Resolved
                "resolution_notes": resolution_notes,
                "close_code": close_reason,
                "closed_by": {"name": "Incident Agent"},
                "closed_at": "javascript:gs.nowDateTime()"
            }

            response = self.session.patch(
                f"{self.api_url}/table/incident/{incident_id}",
                headers=self._get_headers(),
                json=update_data,
                timeout=self.timeout
            )

            if response.status_code == 200:
                logger.info(f"Successfully closed incident {incident_id}")
                return True
            else:
                logger.error(f"Error closing incident {incident_id}: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error closing incident: {str(e)}")
            return False

    def get_reporter_approval_field(self, incident_id: str) -> Optional[str]:
        """
        Get custom approval field value for reporter confirmation.

        Args:
            incident_id: ServiceNow incident sys_id

        Returns:
            Approval status or None
        """
        try:
            response = self.session.get(
                f"{self.api_url}/table/incident/{incident_id}",
                headers=self._get_headers(),
                params={"sysparm_fields": "sys_id,reporter_approval,u_reporter_approved"},
                timeout=self.timeout
            )

            if response.status_code == 200:
                results = response.json().get("result", [])
                if results:
                    incident = results[0]
                    # Check for approval field (could be u_reporter_approved or custom field)
                    approval = incident.get("reporter_approval") or incident.get("u_reporter_approved")
                    return approval
            return None

        except Exception as e:
            logger.error(f"Error getting reporter approval: {str(e)}")
            return None

    def get_incident_reporter(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """
        Get reporter information for an incident.

        Args:
            incident_id: ServiceNow incident sys_id

        Returns:
            Reporter info dict with name, email, etc or None
        """
        try:
            response = self.session.get(
                f"{self.api_url}/table/incident/{incident_id}",
                headers=self._get_headers(),
                params={"sysparm_fields": "caller_id,reporter"},
                timeout=self.timeout
            )

            if response.status_code == 200:
                results = response.json().get("result", [])
                if results:
                    incident = results[0]
                    reporter_ref = incident.get("caller_id") or incident.get("reporter")
                    if isinstance(reporter_ref, dict) and "value" in reporter_ref:
                        return reporter_ref
                    return reporter_ref
            return None

        except Exception as e:
            logger.error(f"Error getting reporter info: {str(e)}")
            return None

    def get_category_options(self) -> List[str]:
        """
        Get list of valid incident categories in ServiceNow.

        Returns:
            List of category strings
        """
        # Mock for now - in production, this would query ServiceNow
        categories = [
            "Infrastructure",
            "Database",
            "Networking",
            "Application",
            "Security",
            "Hardware",
            "Email",
            "VPN",
            "Storage",
            "Backup"
        ]
        return categories

    def create_incident(self, title: str, description: str, category: str = "Application",
                       priority: str = "3", urgency: str = "2", impact: str = "2",
                       assignment_group: str = None) -> Optional[Dict[str, Any]]:
        """
        Create a new incident in ServiceNow.

        Args:
            title: Short description/title
            description: Detailed description
            category: Incident category
            priority: Priority (1-5, lower is higher)
            urgency: Urgency (1-5)
            impact: Impact (1-5)
            assignment_group: Optional assignment group name

        Returns:
            Created incident dict with sys_id and number, or None if failed
        """
        try:
            incident_data = {
                "short_description": title,
                "description": description,
                "category": category,
                "priority": priority,
                "urgency": urgency,
                "impact": impact
            }

            # Add assignment group if provided
            if assignment_group:
                group_id = self._get_assignment_group_id(assignment_group)
                if group_id:
                    incident_data["assignment_group"] = group_id

            response = self.session.post(
                f"{self.api_url}/table/incident",
                headers=self._get_headers(),
                json=incident_data,
                timeout=self.timeout
            )

            if response.status_code == 201:
                result = response.json().get("result", {})
                inc_number = result.get("number")
                inc_id = result.get("sys_id")
                logger.info(f"Created incident {inc_number} ({inc_id})")
                return result
            else:
                logger.error(f"Error creating incident: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error creating incident: {str(e)}")
            return None

    def delete_incident(self, incident_id: str) -> bool:
        """
        Delete an incident from ServiceNow.

        Args:
            incident_id: ServiceNow incident sys_id

        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.session.delete(
                f"{self.api_url}/table/incident/{incident_id}",
                headers=self._get_headers(),
                timeout=self.timeout
            )

            if response.status_code == 204:
                logger.info(f"Successfully deleted incident {incident_id}")
                return True
            else:
                logger.error(f"Error deleting incident {incident_id}: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error deleting incident: {str(e)}")
            return False

    def delete_all_incidents(self, state: List[str] = None) -> int:
        """
        Delete all incidents in given states.

        Args:
            state: List of state values to delete (1=New, 2=In Progress, etc)

        Returns:
            Number of incidents deleted
        """
        try:
            # Fetch all incidents in the specified states
            incidents = self.get_new_incidents(state=state, limit=100)
            
            deleted_count = 0
            for incident in incidents:
                incident_id = incident.get("sys_id")
                if self.delete_incident(incident_id):
                    deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} incidents")
            return deleted_count

        except Exception as e:
            logger.error(f"Error deleting all incidents: {str(e)}")
            return 0
