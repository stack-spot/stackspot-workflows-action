import unittest
from unittest.mock import patch, Mock
from script import *
from requests import HTTPError


class TestRunner(unittest.TestCase):

    ##
    # Happy-path
    ##
    @patch('requests.post')
    @patch('requests.get')
    def test_create_repository_in_group_success(self, mock_get, mock_post):
        # scenario
        metadata = Metadata({
            "group_name": "stackspot_group",
            "project_name": "My Java App",
            "visibility": "private",
            "token": "valid-token"
        })
        mock_get.side_effect = [
            Mock(status_code=200, json=lambda: [{"name": "stackspot_group", "id": 123}]),
            Mock(status_code=200, json=lambda: [
                {"id": 1, "name": "project 1", "path": "project1"},
                {"id": 2, "name": "project 2", "path": "project2"},
                {"id": 3, "name": "project 3", "path": "project3"}
            ])
        ]
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"id": 24, "name": "My Java App", "path": "my-java-app"}

        # action
        runner = Runner(metadata, "http://localhost:9090")
        runner()

        # validation
        mock_post.assert_called_once_with(
            "http://localhost:9090/api/v4/projects",
            json={
                "name": metadata.get("project_name"),
                "namespace_id": 123,
                "visibility": metadata.get("visibility"),
            },
            headers={
                "Private-Token": "valid-token",
                "Content-Type": "application/json"
            },
            timeout=10,
            verify=True
        )

    def test_inputs_has_default_values(self):
        # scenario
        empty_metadata = Metadata({})

        # action
        runner = Runner(empty_metadata)

        # validation
        self.assertEqual("https://gitlab.com", runner.base_url, "Gitlab base URL")
        self.assertEqual("private", runner.visibility, "visibility type")
        self.assertEqual(True, runner.enable_ssl_verify, "(dev) enable HTTP SSL verify")
        self.assertEqual(10, runner.default_timeout, "(dev) default HTTP timeout")
        self.assertEqual(False, runner.enable_logging, "(dev) enable HTTP logging")

    def test_group_name_is_not_informed_error(self):
        # scenario
        metadata = Metadata({
            "token": "valid-token-injected-by-portal"
        })

        # action and validation
        with self.assertRaises(InvalidInputException) as em:
            runner = Runner(metadata, "http://localhost:9090")
            runner()
        self.assertEqual("The group name ('group_name') must not be blank.", str(em.exception))

    def test_group_name_is_blank_error(self):
        # scenario
        metadata = Metadata({
            "group_name": (" " * 10),
            "token": "valid-token-injected-by-portal"
        })

        # action and validation
        with self.assertRaises(InvalidInputException) as em:
            runner = Runner(metadata, "http://localhost:9090")
            runner()
        self.assertEqual("The group name ('group_name') must not be blank.", str(em.exception))

    def test_token_is_not_informed_error(self):
        # scenario
        metadata = Metadata({
            "group_name": "valid-group"
        })

        # action and validation
        with self.assertRaises(InvalidInputException) as em:
            runner = Runner(metadata, "http://localhost:9090")
            runner()
        self.assertEqual("The private token ('token') must not be blank.", str(em.exception))

    def test_token_is_blank_error(self):
        # scenario
        metadata = Metadata({
            "group_name": "valid-group",
            "token": (" " * 10)
        })

        # action and validation
        with self.assertRaises(InvalidInputException) as em:
            runner = Runner(metadata, "http://localhost:9090")
            runner()
        self.assertEqual("The private token ('token') must not be blank.", str(em.exception))

    def test_project_name_is_not_informed_error(self):
        # scenario
        metadata = Metadata({
            "group_name": "my_group",
            "token": "valid-token"
        })

        # action and validation
        with self.assertRaises(InvalidInputException) as em:
            runner = Runner(metadata, "http://localhost:9090")
            runner()
        self.assertEqual("The project name ('project_name') must not be blank.", str(em.exception))

    def test_project_name_is_blank_error(self):
        # scenario
        metadata = Metadata({
            "group_name": "my_group",
            "project_name": (" " * 10),
            "token": "valid-token"
        })

        # action and validation
        with self.assertRaises(InvalidInputException) as em:
            runner = Runner(metadata, "http://localhost:9090")
            runner()
        self.assertEqual("The project name ('project_name') must not be blank.", str(em.exception))

    def test_project_name_is_too_short_error(self):
        # scenario
        metadata = Metadata({
            "group_name": "my_group",
            "project_name": "p1",
            "token": "valid-token"
        })

        # action and validation
        with self.assertRaises(InvalidInputException) as em:
            runner = Runner(metadata, "http://localhost:9090")
            runner()
        self.assertEqual(
            "The project name 'p1' is too short. It must contain at least 3 characters.",
            str(em.exception)
        )

    def test_project_name_is_too_short_with_whitespaces_error(self):
        # scenario
        project_name_with_whitespaces = "   p2   "
        metadata = Metadata({
            "group_name": "my_group",
            "project_name": project_name_with_whitespaces,
            "token": "valid-token"
        })

        # action and validation
        with self.assertRaises(InvalidInputException) as em:
            runner = Runner(metadata, "http://localhost:9090")
            runner()
        self.assertEqual(
            f"The project name '{project_name_with_whitespaces}' is too short. It must contain at least 3 characters.",
            str(em.exception)
        )

    def test_visibility_type_is_blank_error(self):
        # scenario
        blank_visibility = (" " * 10)
        metadata = Metadata({
            "group_name": "my_group",
            "project_name": "my-project",
            "visibility": blank_visibility,
            "token": "valid-token"
        })

        # action and validation
        with self.assertRaises(InvalidInputException) as em:
            runner = Runner(metadata, "http://localhost:9090")
            runner()
        self.assertEqual("The visibility type ('visibility') must not be blank.", str(em.exception))

    def test_visibility_type_is_invalid_error(self):
        # scenario
        invalid_visibility = "internal"
        metadata = Metadata({
            "group_name": "my_group",
            "project_name": "my-project",
            "visibility": invalid_visibility,
            "token": "valid-token"
        })

        # action and validation
        with self.assertRaises(InvalidInputException) as em:
            runner = Runner(metadata, "http://localhost:9090")
            runner()
        self.assertEqual(
            f"The visibility type informed is invalid: '{invalid_visibility}'. It must be 'public' or 'private'.",
            str(em.exception)
        )

    @patch('requests.get')
    def test_group_not_found_error(self, mock_get):
        # scenario
        metadata = Metadata({
            "group_name": "invalid-group",
            "project_name": "blank-project",
            "token": "valid-token"
        })
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{"name": "group1", "id": 1}, {"name": "group2", "id": 2}]

        # action and validation
        with self.assertRaises(GroupNotFound) as em:
            runner = Runner(metadata, "http://localhost:9090")
            runner()
        self.assertEqual(f"The 'invalid-group' group was not found.", str(em.exception))

    @patch('requests.get')
    def test_project_already_exists_in_name_error(self, mock_get):
        # scenario
        metadata = Metadata({
            "group_name": "stackspot_group",
            "project_name": "Existing project",
            "token": "valid-token"
        })
        mock_get.side_effect = [
            Mock(status_code=200, json=lambda: [{"name": "stackspot_group", "id": 123}]),
            Mock(status_code=200, json=lambda: [
                {"id": 1, "name": "Simple project", "path": "simple-project"},
                {"id": 2, "name": metadata.get("project_name"), "path": "existing-project-app"},
                {"id": 3, "name": "Another java project", "path": "another-java-project"}
            ])
        ]

        # action and validation
        with self.assertRaises(ProjectAlreadyExistsInTheGroup) as em:
            runner = Runner(metadata, "http://localhost:9090")
            runner()
        self.assertEqual(
            "The project (repository) 'Existing project' already exists in the group 'stackspot_group' (group_id=123).",
            str(em.exception)
        )

    @patch('requests.get')
    def test_project_already_exists_in_path_error(self, mock_get):
        # scenario
        metadata = Metadata({
            "group_name": "stackspot_group",
            "project_name": "existing-project",
            "token": "valid-token"
        })
        mock_get.side_effect = [
            Mock(status_code=200, json=lambda: [{"name": "stackspot_group", "id": 456}]),
            Mock(status_code=200, json=lambda: [
                {"id": 1, "name": "Simple project", "path": "simple-project"},
                {"id": 2, "name": "Existing project App", "path": metadata.get("project_name")},
                {"id": 3, "name": "Another java project", "path": "another-java-project"}
            ])
        ]

        # action and validation
        with self.assertRaises(ProjectAlreadyExistsInTheGroup) as em:
            runner = Runner(metadata, "http://localhost:9090")
            runner()
        self.assertEqual(
            "The project (repository) 'existing-project' already exists in the group 'stackspot_group' (group_id=456).",
            str(em.exception)
        )

    ##
    # Validates a possible race condition scenario when creating a repository
    ##
    @patch('requests.post')
    @patch('requests.get')
    def test_create_repository_in_group_when_project_already_exists_error(self, mock_get, mock_post):
        # scenario
        metadata = Metadata({
            "group_name": "group1",
            "project_name": "my repo",
            "visibility": "public",
            "token": "valid-token"
        })
        mock_get.side_effect = [
            Mock(status_code=200, json=lambda: [{"name": "group1", "id": 123}]),
            Mock(status_code=200, json=lambda: [])
        ]

        mock_post.return_value = self.__mock_http_error_400_with_payload(json={
            "message": {
                "project_namespace.name": [
                    "has already been taken"
                ],
                "name": [
                    "has already been taken"
                ],
                "path": [
                    "has already been taken"
                ]
            }
        })

        # action and validation
        with self.assertRaises(GitlabCreateRepoException) as em:
            runner = Runner(metadata, "http://localhost:9090")
            runner()
        self.assertEqual(
            f"Error while creating project (repository) 'my repo' in the group 'group1': Project already exists in the group. (possible race condition)",
            str(em.exception)
        )

    @patch('requests.get')
    def test_group_unexpected_error(self, mock_get):
        # scenario
        metadata = Metadata({
            "group_name": "group1",
            "project_name": "blank-project",
            "token": "valid-token"
        })
        mock_get.return_value = self.__mock_http_error_401()

        # action and validation
        with self.assertRaises(GitlabCreateRepoException) as em:
            runner = Runner(metadata, "http://localhost:9090")
            runner()
        self.assertEqual(f"Error while searching for group_id by the group name 'group1': 401-Unauthorized", str(em.exception))

    @patch('requests.get')
    def test_project_unexpected_error(self, mock_get):
        # scenario
        metadata = Metadata({
            "group_name": "group1",
            "project_name": "my-new-project",
            "token": "valid-token"
        })
        mock_get.side_effect = [
            Mock(status_code=200, json=lambda: [{"name": "group1", "id": 123}]),
            self.__mock_http_error_401()
        ]

        # action and validation
        with self.assertRaises(GitlabCreateRepoException) as em:
            runner = Runner(metadata, "http://localhost:9090")
            runner()
        self.assertEqual(
            "Error while checking if project (repository) 'my-new-project' already exists in the group 'group1 (group_id=123)': 401-Unauthorized",
            str(em.exception)
        )

    @staticmethod
    def __mock_http_error_400_with_payload(json):
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = HTTPError("Bad Request", response=mock_response)
        mock_response.text = str(json)
        mock_response.json.return_value = json
        return mock_response

    @staticmethod
    def __mock_http_error_401():
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = HTTPError("401-Unauthorized: Private Token invalid or not informed", response=mock_response)
        mock_response.text = "401-Unauthorized"
        return mock_response

class Metadata:
    def __init__(self, inputs):
        self.inputs = inputs

    def get(self, key):
        return self.inputs.get(key)


if __name__ == "__main__":
    unittest.main()
