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
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const ContainersPage = () => {
  const [file, setFile] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [containers, setContainers] = useState([]);

  useEffect(() => {
    fetchFeedbackMessages();
    fetchUploadedFiles();
    fetchContainers();

    const refreshInterval = setInterval(() => {
      fetchContainers();
      fetchFeedbackMessages();
      fetchUploadedFiles();
    }, 5000); // Refresh every 5 seconds

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
      toast.error("Please select a JAR, WAR, or SH file to upload.");
      return;
    }

    try {
      const formData = new FormData();
      formData.append("file", file);

      await axios.post(`${BACKEND_URL}/upload`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      toast.success("File uploaded successfully");
      fetchUploadedFiles();
    } catch (error) {
      toast.error("Failed to upload the file. Please try again later.");
    }
  };

  const handleCreateContainer = async (fileName) => {
    const requestBody = {
      fileId: fileName,
    };

    try {
      await axios.post(`${BACKEND_URL}/containers/create`, requestBody);
      toast.success("Sent request to create a new container");
      fetchContainers();
    } catch (error) {
      toast.error("Failed to create a new container. Please try again later.");
    }
  };

  const handleDeleteFile = async (fileName) => {
    try {
      await axios.delete(`${BACKEND_URL}/upload/files/${fileName}`);
      toast.success("File deleted successfully");
      fetchUploadedFiles();
    } catch (error) {
      toast.error("Failed to delete the file. Please try again later.");
    }
  };

  const handleDeleteContainer = async (containerId) => {
    console.log("Deleting container:", containerId);
    try {
      await axios.delete(`${BACKEND_URL}/containers/${containerId}`);
      toast.success("Sent request to delete container");
      fetchContainers();
    } catch (error) {
      toast.error("Failed to delete the container. Please try again later.");
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
      toast.error("Failed to fetch containers. Please try again later.");
    }
  };

  // This function fetches errors from the backend
  const fetchFeedbackMessages = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/containers/errors`);
      // Assuming the response contains an array of error messages
      response.data.forEach((message) => {
        if (message.level === "INFO") {
          toast.info(message.message);
        }

        if (message.level === "WARNING") {
          toast.warn(message.message);
        }

        if (message.level === "ERROR") {
          toast.error(message.message);
        }

        if (message.level === "SUCCESS") {
          toast.success(message.message);
        }
      });
    } catch (error) {
      console.error("Failed to fetch errors:", error);
    }
  };

  return (
    <Container>
      <CustomNavbar />
      <ToastContainer />

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
            <Button type="submit" className="mt-3">
              Upload
            </Button>
          </Form>
        </Card.Body>
      </Card>

      <Card className="my-4">
        <Card.Body>
          <h3 className="mb-4">Uploaded Files</h3>
          {uploadedFiles.map((file) => (
            <Card className="mb-3" key={file.id}>
              <Card.Body>
                <strong>Name:</strong> {file.name}
                <br />
                <strong>Type:</strong> {file.type}
                <br />
                <strong>Size:</strong> {file.size}
              </Card.Body>
              <Card.Footer>
                <Button
                  className="mt-3 mr-2"
                  onClick={() => handleCreateContainer(file.name)}
                  variant="outline-primary"
                  style={{ borderRadius: "20px" }}
                >
                  Create Container
                </Button>
                <Button
                  className="mt-3"
                  onClick={() => handleDeleteFile(file.name)}
                  variant="outline-danger"
                  style={{ borderRadius: "20px", marginLeft: "10px" }}
                >
                  Delete File
                </Button>
              </Card.Footer>
            </Card>
          ))}
        </Card.Body>
      </Card>

      <Card className="my-4">
        <Card.Body>
          <h3 className="mb-4">Containers</h3>
          {containers.length === 0 ? (
            <p>No containers found.</p>
          ) : (
            containers.map((container, index) => (
              <Card key={index} className="mb-3">
                <Card.Body>
                  <strong>ID:</strong> {container.id}
                  <br />
                  <strong>Name:</strong> {container.name}
                  <br />
                  <strong>Status:</strong> {container.status}
                  <br />
                  <strong>Ip Address:</strong> {container.ip}
                  <br />
                  <strong>Image:</strong> {container.image}
                  <br />
                  <strong>Created At:</strong> {container.created}
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
            ))
          )}
        </Card.Body>
      </Card>
    </Container>
  );
};

export default ContainersPage;
