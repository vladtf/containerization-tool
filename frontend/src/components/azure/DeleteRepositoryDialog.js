import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";
import axios from "axios";
import { Button } from "react-bootstrap";
import { toast } from "react-toastify";
import { PYTHON_BACKEND_URL } from "../../config/BackendConfiguration";

const DeleteRepositoryDialog = ({
  openDeleteRepositoryDialog,
  setOpenDeleteRepositoryDialog,
  selectedRepository,
  fetchAzureContainerRepositories,
}) => {
  const handleDeleteRepository = (repositoryName) => {
    console.log("Deleting repository:", repositoryName);
    toast.success("Deleting repository: " + repositoryName);

    axios
      .delete(`${PYTHON_BACKEND_URL}/azure/repository/${repositoryName}`)
      .then((response) => {
        console.log(response);
        toast.success(
          "Repository '" + repositoryName + "' deleted successfully"
        );
        fetchAzureContainerRepositories();
      })
      .catch((error) => {
        console.error(error);
        toast.error("Failed to delete repository: " + error.response.data);
      });
  };

  return (
    <Dialog
      open={openDeleteRepositoryDialog}
      onClose={() => setOpenDeleteRepositoryDialog(false)}
    >
      <DialogTitle>Delete Repository</DialogTitle>
      <DialogContent>
        <DialogContentText>
          Are you sure you want to delete this repository: {selectedRepository}?
        </DialogContentText>
      </DialogContent>

      <DialogActions>
        <Button
          variant="primary"
          onClick={() => setOpenDeleteRepositoryDialog(false)}
        >
          Cancel
        </Button>
        <Button
          variant="outline-danger"
          onClick={() => {
            setOpenDeleteRepositoryDialog(false);
            handleDeleteRepository(selectedRepository);
          }}
        >
          Delete
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default DeleteRepositoryDialog;