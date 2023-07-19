import React, { useState, useEffect } from "react";
import { Button, Card } from "react-bootstrap";
import axios from "axios";
import { ToastContainer, toast } from "react-toastify";
import { BACKEND_URL } from "../../config/BackendConfiguration";

const ContainersData = () => {
  const [containers, setContainers] = useState([]);

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
    </>
  );
};

export default ContainersData;
