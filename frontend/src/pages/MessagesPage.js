import React, { useState, useEffect } from "react";
import { Container, ListGroup, Alert, Button } from "react-bootstrap";
import CustomNavbar from "../components/CustomNavbar";
import axios from "axios";

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
      const response = await axios.get("http://localhost:8180/messages/all");
      setMessages(response.data);
      setError(null);
    } catch (error) {
      setError("Failed to fetch messages.");
    }
  };

  const handleClearMessages = async () => {
    try {
      await axios.get("http://localhost:8180/messages/clear");
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
      <div>
        <h1>Messages Page</h1>
        {error && <Alert variant="danger">{error}</Alert>}
        {Object.keys(groupedMessages).length === 0 && !error && (
          <Alert variant="info">No messages available.</Alert>
        )}
        <Button variant="danger" onClick={handleClearMessages}>
          Clear Messages
        </Button>
        
        {Object.keys(groupedMessages).length > 0 && (
          <ListGroup>
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
      </div>
    </Container>
  );
};

export default MessagesPage;
