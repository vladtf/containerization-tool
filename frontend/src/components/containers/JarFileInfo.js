import axios from "axios";
import { useEffect, useState } from "react";
import { Button, Modal } from "react-bootstrap";
import { BACKEND_URL } from "../../config/BackendConfiguration";
import { ToastContainer, toast } from "react-toastify";

const JarFileInfo = ({ displayJarInfo, setDisplayJarInfo, file }) => {
  const [jarFile, setJarFile] = useState(null);

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

    axios
      .post(`${BACKEND_URL}/upload/jar`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      })
      .then((response) => {
        setJarInfo(response.data);
      })
      .catch((error) => {
        console.log(error);
        toast.error("Error getting jar file info");
        setDisplayJarInfo(false);
      });
  }, [file]);

  // Function to send a request to the backend confirming the selection
  const sendSelectionToBackend = (className) => {
    console.log(`Sending selection to backend: ${className}`);
  };
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
          <Modal.Title>File Info</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {!jarInfo ? (
            <p>No info available</p>
          ) : (
            <>
              <p>
                <strong>Main method in manifest:</strong>{" "}
                {jarInfo.mainClassName ? (
                  <>
                    {jarInfo.mainClassName}
                    <Button
                      onClick={() => {
                        sendSelectionToBackend(jarInfo.mainClassName);
                      }}
                      variant="outline-primary"
                      style={{ borderRadius: "20px" }}
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
              {jarInfo.classesWithMainMethod.map((className) => (
                <div key={className}>
                  <span>{className}</span>
                  <Button
                    onClick={() => {
                      sendSelectionToBackend(className);
                    }}
                    variant="outline-primary"
                    style={{ borderRadius: "20px" }}
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
            style={{ borderRadius: "20px" }}
          >
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
};

export default JarFileInfo;
