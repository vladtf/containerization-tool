import React, { useState, useEffect } from "react";
import { Container, Alert, Form, Button, ListGroup } from "react-bootstrap";
import CustomNavbar from "../components/CustomNavbar";
import axios from "axios";
import { BACKEND_URL } from "../config/BackendConfiguration";

const CreateContainerPage = () => {
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [file, setFile] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);

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
  }, []);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    setFile(selectedFile);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!file) {
      setError("Please select a JAR or WAR file to upload.");
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

  const fetchUploadedFiles = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/upload/files`);
      setUploadedFiles(response.data);
    } catch (error) {
      console.error("Failed to fetch uploaded files:", error);
    }
  };

  return (
    <Container>
      <CustomNavbar />
      {error && <Alert variant="danger">{error}</Alert>}
      {success && <Alert variant="success">Request sent successfully!</Alert>}

      <Form onSubmit={handleSubmit}>
        <Form.Group>
          <Form.Label>Select JAR or WAR File:</Form.Label>
          <Form.Control
            type="file"
            accept=".jar,.war,.sh"
            onChange={handleFileChange}
          />
        </Form.Group>
        <Button type="submit">Upload</Button>
      </Form>

      <ListGroup className="mt-4">
        {uploadedFiles.map((file, index) => (
          <ListGroup.Item key={index}>
            <div>
              <strong>Name:</strong> {file.name}
            </div>
            <div>
              <strong>Type:</strong> {file.type}
            </div>
            <div>
              <strong>Size:</strong> {file.size}
            </div>
          </ListGroup.Item>
        ))}
      </ListGroup>
    </Container>
  );
};

export default CreateContainerPage;
