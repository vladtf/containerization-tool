import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";
import axios from "axios";
import { Button } from "react-bootstrap";
import { toast } from "react-toastify";
import { PYTHON_BACKEND_URL } from "../../config/BackendConfiguration";

const DeleteContainerDialog = ({
  openDeleteContainerDialog,
  setOpenDeleteContainerDialog,
  container,
  fetchContainers,
  setSelectedContainer,
}) => {
  const handleDeleteContainer = async (container) => {
    const containerId = container.id;

    console.log("Deleting container:", containerId);

    axios
      .delete(`${PYTHON_BACKEND_URL}/azure/container/${containerId}`)
      .then((response) => {
        console.log(response);
        toast.success("Container deleted successfully");

        setSelectedContainer("");
        fetchContainers();
      })
      .catch((error) => {
        console.error(error);
        toast.error("Failed to delete container: " + error.response.data);
      });
  };

  return (
    <Dialog
      open={openDeleteContainerDialog}
      onClose={() => setOpenDeleteContainerDialog(false)}
    >
      <DialogTitle>Delete Container</DialogTitle>
      <DialogContent>
        <DialogContentText>
          Are you sure you want to delete this container:
          {container && container.name}?
        </DialogContentText>
      </DialogContent>

      <DialogActions>
        <Button
          variant="primary"
          onClick={() => setOpenDeleteContainerDialog(false)}
        >
          Cancel
        </Button>
        <Button
          variant="outline-danger"
          onClick={() => {
            setOpenDeleteContainerDialog(false);
            handleDeleteContainer(container);
          }}
        >
          Delete
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default DeleteContainerDialog;
