import torch


def RMSELoss(outputs, targets, optimizer, data):
    """Default loss function

    If user does not input loss function we provide mean-squared error loss
    function.

    Parameters
    ----------
    outputs : tensor
        Outputs of the model.
    targets : tensor
        Expected value of outputs.
    optimizer : obj
        An optimizer object to minimize the loss function error.
    data : obj
        A data object from mlchem.

    Returns
    -------
    loss : tensor
        The value of the loss function.
    rmse : float
        Value of the root-mean squared error per atom.
    """

    optimizer.zero_grad()  # clear previous gradients

    criterion = torch.nn.MSELoss(reduction='sum')
    atoms_per_image = torch.tensor(data.atoms_per_image,
                                   requires_grad=False,
                                   dtype=torch.float)
    outputs_atom = torch.div(outputs, atoms_per_image)
    targets_atom = torch.div(targets, atoms_per_image)

    loss = criterion(outputs_atom, targets_atom) * .5
    loss.backward()
    optimizer.step()

    rmse = torch.sqrt(loss).item()

    return loss, rmse

def RMSELossAE(outputs, targets, optimizer):
    """Default loss function

    If user does not input loss function we provide mean-squared error loss
    function.

    Parameters
    ----------
    outputs : tensor
        Outputs of the model.
    targets : tensor
        Expected value of outputs.
    optimizer : obj
        An optimizer object to minimize the loss function error.

    Returns
    -------
    loss : tensor
        The value of the loss function.
    rmse : float
        Value of the root-mean squared error per atom.
    """

    optimizer.zero_grad()  # clear previous gradients

    criterion = torch.nn.MSELoss(reduction='sum')
    loss = criterion(outputs, targets)
    loss.backward()
    optimizer.step()
    rmse = torch.sqrt(loss).item()

    return loss, rmse
