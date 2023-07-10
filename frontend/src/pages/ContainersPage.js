import React, { useState, useEffect } from "react";
import {
  Container,
  Alert,
  Form,
  Button,
  ListGroup,
  Card,
} from "react-bootstrap";
import CustomNavbar from "../components/CustomNavbar";
import axios from "axios";
import { BACKEND_URL } from "../config/BackendConfiguration";

const ContainersPage = () => {
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [file, setFile] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [containers, setContainers] = useState([]);

  useEffect(() => {
    let errorTimeout, successTimeout;

    if (error) {
      errorTimeout = setTimeout(() => {
        setError("");
      }, 3000);
    }

    if (success) {
      successTimeout = setTimeout(() => {
        setSuccess(false);
      }, 3000);
    }

    return () => {
      clearTimeout(errorTimeout);
      clearTimeout(successTimeout);
    };
  }, [error, success]);

  useEffect(() => {
    fetchUploadedFiles();
    fetchContainers();

    const refreshInterval = setInterval(() => {
      fetchContainers();
    }, 5000); // Refresh containers every 5 seconds

    return () => {
      clearInterval(refreshInterval);
    };
  }, []);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    setFile(selectedFile);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!file) {
      setError("Please select a JAR, WAR, or SH file to upload.");
      return;
    }

    setError("");
    setSuccess(false);

    try {
      const formData = new FormData();
      formData.append("file", file);

      await axios.post(`${BACKEND_URL}/upload`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setSuccess(true);
      fetchUploadedFiles();
    } catch (error) {
      setError("Failed to upload the file. Please try again later.");
    }
  };

  const handleCreateContainer = async (fileName) => {
    const requestBody = {
      fileId: fileName,
    };

    try {
      await axios.post(`${BACKEND_URL}/containers/create`, requestBody);
      setSuccess(true);
      fetchContainers();
    } catch (error) {
      setError("Failed to create a new container. Please try again later.");
    }
  };

  const handleDeleteContainer = async (containerId) => {
    console.log("Deleting container:", containerId);
    try {
      await axios.delete(`${BACKEND_URL}/containers/${containerId}`);
      setSuccess(true);
      fetchContainers();
    } catch (error) {
      setError("Failed to delete the container. Please try again later.");
    }
  };

  const fetchUploadedFiles = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/upload/files`);
      setUploadedFiles(response.data);
    } catch (error) {
      console.error("Failed to fetch uploaded files:", error);
    }
  };

  const fetchContainers = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/containers`);
      setContainers(response.data);
    } catch (error) {
      console.error("Failed to fetch containers:", error);
    }
  };

  return (
    <Container>
      <CustomNavbar />
      {error && <Alert variant="danger">{error}</Alert>}
      {success && <Alert variant="success">Request sent successfully!</Alert>}

      <Card className="my-4">
        <Card.Body>
          <h3 className="mb-4">Upload File</h3>
          <Form onSubmit={handleSubmit}>
            <Form.Group>
              <Form.Label>Select JAR, WAR, or SH File:</Form.Label>
              <Form.Control
                type="file"
                accept=".jar,.war,.sh"
                onChange={handleFileChange}
              />
            </Form.Group>
            <Button type="submit">Upload</Button>
          </Form>
        </Card.Body>
      </Card>

      <Card className="my-4">
        <Card.Body>
          <h3 className="mb-4">Uploaded Files</h3>
          {uploadedFiles.map((file, index) => (
            <Card className="mb-3" key={index}>
              <Card.Body>
                <strong>Name:</strong> {file.name}
                <br />
                <strong>Type:</strong> {file.type}
                <br />
                <strong>Size:</strong> {file.size}
              </Card.Body>
              <Card.Footer>
                <Button
                  className="mt-3"
                  onClick={() => handleCreateContainer(file.name)}
                  variant="outline-primary"
                  style={{ borderRadius: "20px" }}
                >
                  Create Container
                </Button>
              </Card.Footer>
            </Card>
          ))}
        </Card.Body>
      </Card>

      <Card className="my-4">
        <Card.Body>
          <h3 className="mb-4">Containers</h3>
          {containers.map((container, index) => (
            <Card key={index} className="mb-3">
              <Card.Body>
                <strong>ID:</strong> {container.id}
                <br />
                <strong>Name:</strong> {container.name}
                <br />
                <strong>Status:</strong> {container.status}
                <br />
                <strong>Image:</strong> {container.image}
              </Card.Body>
              <Card.Footer>
                <Button
                  onClick={() => handleDeleteContainer(container.id)}
                  variant="outline-danger"
                  style={{ borderRadius: "20px" }}
                >
                  Delete Container
                </Button>
              </Card.Footer>
            </Card>
          ))}
        </Card.Body>
      </Card>
    </Container>
  );
};

export default ContainersPage;
