import { Button, Modal } from "react-bootstrap";

const JarFileInfo = ({ displayJarInfo, setDisplayJarInfo, jarInfo }) => {
  // Function to send a request to the backend confirming the selection
  const sendSelectionToBackend = (className) => {
    // Make your API request here to send the selected class to the backend
    // For example, you can use fetch() to send a POST request with the selected class data.
    console.log(`Sending selection to backend: ${className}`);
  };
  return (
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
  );
};

export default JarFileInfo;
