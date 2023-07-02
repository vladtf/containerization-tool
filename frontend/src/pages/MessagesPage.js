import React, { useState, useEffect } from "react";
import { Container, ListGroup, Alert } from "react-bootstrap";
import CustomNavbar from "../components/CustomNavbar";
import axios from "axios";

const MessagesPage = () => {
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get("http://localhost:8180/messages/all");
        setMessages(response.data);
      } catch (error) {
        setError("Failed to fetch messages.");
      }
    };

    fetchData();
  }, []);

  return (
    <Container>
      <CustomNavbar />
      <div>
        <h1>Messages Page</h1>
        {error && <Alert variant="danger">{error}</Alert>}
        {messages.length === 0 && !error && (
          <Alert variant="info">No messages available.</Alert>
        )}
        {messages.length > 0 && (
          <ListGroup>
            {messages.map((message, index) => (
              <ListGroup.Item key={index}>
                <div>
                  <p>Protocol: {message.protocol}</p>
                  <p>Source IP: {message.src_ip}</p>
                  <p>Destination IP: {message.dst_ip}</p>
                  <p>Source Port: {message.src_port || "N/A"}</p>
                  <p>Destination Port: {message.dst_port || "N/A"}</p>
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
