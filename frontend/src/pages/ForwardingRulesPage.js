import React, { useState, useEffect } from "react";
import { Container, ListGroup, Alert } from "react-bootstrap";
import CustomNavbar from "../components/CustomNavbar";
import axios from "axios";

const ForwardingRulesPage = () => {
  const [data, setData] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get(
          "http://localhost:8180/forwarding-chains/all"
        );
        setData(response.data);
      } catch (error) {
        setError("Error fetching data");
      }
    };

    fetchData();
  }, []);

  return (
    <Container>
      <CustomNavbar />
      {error && <Alert variant="danger">{error}</Alert>}
      <ListGroup>
        {data.map((item, index) => (
          <ListGroup.Item key={index}>
            <h5>{item.name}</h5>
            <ul>
              {item.rules.map((rule, ruleIndex) => (
                <li key={ruleIndex}>
                  <strong>Rule {ruleIndex + 1}</strong>
                  <ul>
                    <li>Name: {rule.name}</li>
                    <li>Target: {rule.target}</li>
                    <li>Protocol: {rule.protocol}</li>
                    <li>Options: {rule.options}</li>
                    <li>Source: {rule.source}</li>
                    <li>Destination: {rule.destination}</li>
                    <li>
                      Extra:{" "}
                      {rule.extra.map((extraItem, extraIndex) => (
                        <span key={extraIndex}>{extraItem}, </span>
                      ))}
                    </li>
                  </ul>
                </li>
              ))}
            </ul>
          </ListGroup.Item>
        ))}
      </ListGroup>
    </Container>
  );
};

export default ForwardingRulesPage;
