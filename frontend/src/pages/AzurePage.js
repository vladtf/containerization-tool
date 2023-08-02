import { Button, Container } from "react-bootstrap";
import CustomNavbar from "../components/CustomNavbar";
import { ToastContainer, toast } from "react-toastify";
import CustomFooter from "../components/CustomFooter";
import { PYTHON_BACKEND_URL } from "../config/BackendConfiguration";
import axios from "axios";
import { useEffect, useState } from "react";
import { IoCubeOutline } from "react-icons/io5";

const AzurePage = () => {
  const [loading, setLoading] = useState(false);
  const [containers, setContainers] = useState([]);
  const [selectedContainer, setSelectedContainer] = useState("");

  useEffect(() => {
    fetchContainers();

    const refreshInterval = setInterval(() => {
      fetchContainers();
    }, 2000); // Refresh data

    return () => {
      clearInterval(refreshInterval);
    };
  }, []);

  const fetchContainers = async () => {
    try {
      const response = await axios.get(`${PYTHON_BACKEND_URL}/azure/all`);
      setContainers(response.data);
    } catch (error) {
      console.error("Failed to fetch containers:", error);
      toast.error("Failed to fetch containers. Please try again later.");
    }
  };

  return (
    <Container>
      <CustomNavbar />
      <ToastContainer />

      <div style={{ overflowX: "scroll", display: "flex" }}>
        {containers.map((container) => (
          <Button
            key={container.id}
            style={{
              margin: "0 5px",
              width: "180px",
              height: "180px",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              position: "relative",
            }}
            variant={
              selectedContainer === container.id ? "primary" : "outline-primary"
            }
            onClick={() => setSelectedContainer(container.id)}
          >
            <div
              style={{
                position: "absolute",
                top: 0,
                left: "50%",
                transform: "translateX(-50%)",
              }}
            >
              <IoCubeOutline size={40} />
            </div>
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                height: "100%",
              }}
            >
              <span>{container.name}</span>
            </div>
          </Button>
        ))}
      </div>

      <CustomFooter />
    </Container>
  );
};

export default AzurePage;
