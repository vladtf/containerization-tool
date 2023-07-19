import React from "react";
import { Nav } from "react-bootstrap";
import { FaGithub } from "react-icons/fa";

const CustomFooter = () => {
  return (
    <Nav
      className=" bg-dark"
      style={{
        borderTopLeftRadius: "10px",
        borderTopRightRadius: "10px",
        padding: "10px",
        marginTop: "20px",
      }}
    >
      <Nav.Item>
        <Nav.Link
          href="https://github.com/vladtf/containerization-tool"
          target="_blank"
          rel="noopener noreferrer"
        >
          <FaGithub size={20} style={{ marginRight: "5px" }} />
          GitHub
        </Nav.Link>
      </Nav.Item>
    </Nav>
  );
};

export default CustomFooter;
