import axios from "axios";
import React, { useEffect, useState } from "react";
import { Button, Card, Form } from "react-bootstrap";
import { ToastContainer, toast } from "react-toastify";
import { BACKEND_URL } from "../../config/BackendConfiguration";
import JarFileInfo from "./JarFileInfo";

const UploadFile = () => {
  const [file, setFile] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);

  const [displayJarInfo, setDisplayJarInfo] = useState(false);

  const acceptedFileTypes = [".jar", ".war", ".sh", ".py"];

  useEffect(() => {
    fetchUploadedFiles();

    const refreshInterval = setInterval(() => {
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

  const handleFileUpload = async (event) => {
    event.preventDefault();

    if (!file) {
      toast.error("Please select a file to upload");
      return;
    }

    // Get the file extension
    const fileExtension = file.name.split(".").pop();

    if (!acceptedFileTypes.includes(`.${fileExtension}`)) {
      toast.error(
        "Please select a file with one of the following extensions: " +
          acceptedFileTypes.join(", ")
      );
      return;
    }

    if (fileExtension === "jar") {
      setDisplayJarInfo(true);
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

  const fetchUploadedFiles = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/upload/files`);
      setUploadedFiles(response.data);
    } catch (error) {
      console.error("Failed to fetch uploaded files:", error);
    }
  };

  const handleCreateContainer = async (fileName, fileType) => {
    const requestBody = {
      fileId: fileName,
      fileType: fileType,
    };

    try {
      await axios.post(`${BACKEND_URL}/containers/create`, requestBody);
      toast.success("Sent request to create a new container");
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

  return (
    <>
      <ToastContainer />

      <Card className="my-4">
        <Card.Body>
          <h3 className="mb-4">Upload File</h3>
          <Form onSubmit={handleFileUpload}>
            <Form.Group>
              <Form.Label>
                Select a file with one of the following extensions:{" "}
                {acceptedFileTypes.join(", ")}
              </Form.Label>
              <Form.Control
                type="file"
                accept={acceptedFileTypes.join(",")}
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
            <Card className="mb-3" key={file.name}>
              <Card.Body>
                <strong>Name:</strong> {file.name}
                <br />
                <strong>Type:</strong> {file.type}
                {/* If type is jar, display the main class name */}
                {file.type === "JAR" && (
                  <>
                    <br />
                    <strong>Main:</strong> {file.javaMainClass}
                  </>
                )}
                <br />
                <strong>Size:</strong> {file.size}
              </Card.Body>
              <Card.Footer>
                <Button
                  className="mt-3 mr-2"
                  onClick={() => handleCreateContainer(file.name, file.type)}
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

      <JarFileInfo
        displayJarInfo={displayJarInfo}
        setDisplayJarInfo={setDisplayJarInfo}
        file={file}
        fetchUploadedFiles={fetchUploadedFiles}
      />
    </>
  );
};

export default UploadFile;
