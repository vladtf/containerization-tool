import { Container } from "react-bootstrap";
import CustomNavbar from "../components/CustomNavbar";

const HomePage = () => {
  return (
    <Container>
      <CustomNavbar />
      <div>
        <h1>Home Page</h1>
        <p>This is the home page</p>
      </div>
    </Container>
  );
};

export default HomePage;
