import axios from "axios";
import { useEffect, useState } from "react";
import { Button, Modal, Spinner, Alert } from "react-bootstrap";
import { BACKEND_URL } from "../../config/BackendConfiguration";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const JarFileInfo = ({
  displayJarInfo,
  setDisplayJarInfo,
  file,
  fetchUploadedFiles,
}) => {
  const [jarFile, setJarFile] = useState(null);
  const [loading, setLoading] = useState(false);

  const [jarInfo, setJarInfo] = useState({
    classesWithMainMethod: [],
    mainClassName: "",
    mainMethodInManifest: false,
  });

  useEffect(() => {
    if (!file) {
      toast.error("Please select a file to upload");
      setDisplayJarInfo(false);
      return;
    }

    const fileExtension = file.name.split(".").pop();

    if (fileExtension !== "jar") {
      toast.error("Please select a .jar file");
      setDisplayJarInfo(false);
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    axios
      .post(`${BACKEND_URL}/upload/jar/info`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      })
      .then((response) => {
        setJarInfo(response.data);
      })
      .catch((error) => {
        console.error(error);
        toast.error("Error getting jar file info");
        setDisplayJarInfo(false);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [file]);

  const sendSelectionToBackend = (className) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("selectedMainClass", className);

    setLoading(true);
    axios
      .post(`${BACKEND_URL}/upload/jar`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      })
      .then((response) => {
        fetchUploadedFiles();
        toast.success("File uploaded successfully");
      })
      .catch((error) => {
        console.error(error);
        toast.error("Error uploading file: " + error.response.data);
      })
      .finally(() => {
        setLoading(false);
        setDisplayJarInfo(false);
      });
  };

  // Destructure for easier readability
  const { mainClassName, classesWithMainMethod } = jarInfo;

  return (
    <>
      <ToastContainer />

      <Modal
        show={displayJarInfo}
        onHide={() => setDisplayJarInfo(false)}
        size="lg"
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title>Jar Main Class Selection</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {loading ? (
            <Spinner animation="border" variant="primary" />
          ) : !jarInfo ? (
            <Alert variant="danger">No info available</Alert>
          ) : (
            <>
              <p>
                <strong>Main method in manifest:</strong>{" "}
                {mainClassName ? (
                  <>
                    {mainClassName}
                    <Button
                      onClick={() => sendSelectionToBackend(mainClassName)}
                      variant="outline-primary"
                      className="mx-2 rounded-pill"
                    >
                      Confirm Selection
                    </Button>
                  </>
                ) : (
                  <span>N/A</span>
                )}
              </p>
              <p>
                <strong>Classes with main method:</strong>
              </p>
              {classesWithMainMethod.map((className) => (
                <div key={className} className="my-2">
                  <span>{className}</span>
                  <Button
                    onClick={() => sendSelectionToBackend(className)}
                    variant="outline-primary"
                    className="mx-2 rounded-pill"
                  >
                    Confirm Selection
                  </Button>
                </div>
              ))}
            </>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button
            onClick={() => setDisplayJarInfo(false)}
            variant="outline-primary"
            className="rounded-pill"
          >
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
};

export default JarFileInfo;
