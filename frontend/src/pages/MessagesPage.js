import React, { useState, useEffect } from "react";
import { Container, ListGroup, Alert, Button, Card } from "react-bootstrap";
import CustomNavbar from "../components/CustomNavbar";
import axios from "axios";
import { BACKEND_URL } from "../config/BackendConfiguration";

const MessagesPage = () => {
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Fetch data every 5 seconds

    return () => {
      clearInterval(interval); // Clean up the interval on component unmount
    };
  }, []);

  const fetchData = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/messages/all`);
      setMessages(response.data);
      setError(null);
    } catch (error) {
      setError("Failed to fetch messages.");
    }
  };

  const handleClearMessages = async () => {
    try {
      await axios.get(`${BACKEND_URL}/messages/clear`);
      setMessages([]);
      setError(null);
    } catch (error) {
      setError("Failed to clear messages.");
    }
  };

  // Group messages by source and destination
  const groupedMessages = {};
  messages.forEach((message) => {
    const key = `${message.src_ip}-${message.dst_ip}`;
    if (groupedMessages[key]) {
      groupedMessages[key].count += 1;
    } else {
      groupedMessages[key] = {
        message,
        count: 1,
      };
    }
  });

  return (
    <Container>
      <CustomNavbar />
      <Card className="my-4">
        <Card.Body>
          <h3>Messages Page</h3>
          {error && <Alert variant="danger">{error}</Alert>}
          {Object.keys(groupedMessages).length === 0 && !error && (
            <Alert variant="info">No messages available.</Alert>
          )}
          <Button variant="danger" onClick={handleClearMessages}>
            Clear Messages
          </Button>
          {Object.keys(groupedMessages).length > 0 && (
            <ListGroup className="mt-4">
              {Object.values(groupedMessages).map(({ message, count }, index) => (
                <ListGroup.Item key={index}>
                  <div>
                    <p>Protocol: {message.protocol}</p>
                    <p>Source IP: {message.src_ip}</p>
                    <p>Destination IP: {message.dst_ip}</p>
                    <p>Source Port: {message.src_port || "N/A"}</p>
                    <p>Destination Port: {message.dst_port || "N/A"}</p>
                    <p>Count: {count}</p>
                  </div>
                </ListGroup.Item>
              ))}
            </ListGroup>
          )}
        </Card.Body>
      </Card>
    </Container>
  );
};

export default MessagesPage;
