import React, { useState, useEffect } from "react";
import { Button, Card, Modal } from "react-bootstrap";
import axios from "axios";
import { ToastContainer, toast } from "react-toastify";
import { BACKEND_URL, PYTHON_BACKEND_URL } from "../../config/BackendConfiguration";

const ContainersData = () => {
  const [containers, setContainers] = useState([]);
  const [selectedLogs, setSelectedLogs] = useState([]);
  const [showLogsModal, setShowLogsModal] = useState(false); // State to manage log popup visibility
  const [currentPage, setCurrentPage] = useState(1); // Current page number
  const [totalPages, setTotalPages] = useState(1); // Total number of pages
  const [containerId, setContainerId] = useState(null); // Container ID
  const [pageSize, setPageSize] = useState(30); // Number of logs per page

  useEffect(() => {
    fetchFeedbackMessages();
    fetchContainers();

    const refreshInterval = setInterval(() => {
      fetchContainers();
      fetchFeedbackMessages();
    }, 2000); // Refresh data

    return () => {
      clearInterval(refreshInterval);
    };
  }, []);

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
      const response = await axios.get(`${BACKEND_URL}/containers/feedback`);
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

  const fetchContainerLogs = async (containerId, page = 1) => {
    setContainerId(containerId);

    try {
      const response = await axios.get(
        `${BACKEND_URL}/fluentd/logs/${containerId}?page=${page}`
      );
      setSelectedLogs(response.data.content);
      setCurrentPage(response.data.number + 1);
      setTotalPages(response.data.totalPages);
      setPageSize(response.data.size);
      setShowLogsModal(true);
    } catch (error) {
      console.error("Failed to fetch container logs:", error);
      toast.error("Failed to fetch container logs. Please try again later.");
    }
  };

  const handleDeployToAzure = async (container) => {
    console.log("Deploying container:", container);

    axios
      .post(`${PYTHON_BACKEND_URL}/azure/deploy`, container)
      .then((response) => {
        console.log(response);

        // TODO: to show the info about deploy here
        toast.success("Container deployed to Azure: " + response.data);
      })
      .catch((error) => {
        console.error(error);
        toast.error(
          "Failed to deploy container to Azure. Please try again later."
        );
      });

    toast.success("Sent request to deploy container to Azure");
  };

  return (
    <>
      <ToastContainer />
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
                    onClick={() => fetchContainerLogs(container.id)}
                    variant="outline-primary"
                    style={{ borderRadius: "20px", marginRight: "10px" }}
                  >
                    See Logs
                  </Button>

                  <Button
                    onClick={() => handleDeleteContainer(container.id)}
                    variant="outline-danger"
                    style={{ borderRadius: "20px" }}
                  >
                    Delete Container
                  </Button>

                  <Button
                    onClick={() => handleDeployToAzure(container)}
                    variant="outline-success"
                    style={{ borderRadius: "20px", marginLeft: "10px" }}
                  >
                    Deploy to Azure
                  </Button>
                </Card.Footer>
              </Card>
            ))
          )}
        </Card.Body>
      </Card>

      {/* Log Popup */}
      <Modal
        show={showLogsModal}
        onHide={() => setShowLogsModal(false)}
        size="xl"
      >
        <Modal.Header closeButton>
          <Modal.Title>Container Logs</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <pre
            style={{ background: "#f1f1f1", padding: "1rem", overflow: "auto" }}
          >
            {selectedLogs.map((log, index) => (
              <React.Fragment key={index}>
                <span style={{ display: "inline-block" }}>
                  {currentPage * pageSize - pageSize + index + 1}.
                </span>
                {log.message}
                <br />
              </React.Fragment>
            ))}
          </pre>
        </Modal.Body>
        <Modal.Footer>
          <span>{`Page ${currentPage} of ${totalPages}`}</span>
          <Button
            variant="secondary"
            onClick={() => fetchContainerLogs(containerId, currentPage - 1)}
            disabled={currentPage === 1} // Disable previous button on the first page
          >
            Previous
          </Button>
          <Button
            variant="secondary"
            onClick={() => fetchContainerLogs(containerId, currentPage + 1)}
            disabled={currentPage === totalPages} // Disable next button on the last page
          >
            Next
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
};

export default ContainersData;
