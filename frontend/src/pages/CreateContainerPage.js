import React, { useState, useEffect } from "react";
import { Container, Alert, Form, Button } from "react-bootstrap";
import CustomNavbar from "../components/CustomNavbar";
import axios from "axios";
import { BACKEND_URL } from "../config/BackendConfiguration";

const CreateContainerPage = () => {
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [file, setFile] = useState(null);

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

      await axios.post(`${BACKEND_URL}/upload-artifact`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setSuccess(true);
    } catch (error) {
      setError("Failed to upload the file. Please try again later.");
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
          <Form.Control type="file" accept=".jar,.war" onChange={handleFileChange} />
        </Form.Group>
        <Button type="submit">Upload</Button>
      </Form>
    </Container>
  );
};

export default CreateContainerPage;
