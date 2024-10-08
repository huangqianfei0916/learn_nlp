import torch
import torch.nn.functional as F
from pathlib import Path


def cal_loss(pred, gold, trg_pad_idx, smoothing=False):
    ''' Calculate cross entropy loss, apply label smoothing if needed. '''

    gold = gold.contiguous().view(-1)

    if smoothing:
        eps = 0.1
        n_class = pred.size(1)

        one_hot = torch.zeros_like(pred).scatter(1, gold.view(-1, 1), 1)
        one_hot = one_hot * (1 - eps) + (1 - one_hot) * eps / (n_class - 1)
        log_prb = F.log_softmax(pred, dim=1)

        non_pad_mask = gold.ne(trg_pad_idx)
        loss = -(one_hot * log_prb).sum(dim=1)
        loss = loss.masked_select(non_pad_mask).sum()  # average later
    else:
        loss = F.cross_entropy(pred, gold, ignore_index=trg_pad_idx, reduction='sum')
    return loss


def cal_performance(pred, gold, trg_pad_idx, smoothing=False):
    """calculate performance"""
    loss = cal_loss(pred, gold, trg_pad_idx, smoothing=smoothing)

    pred = pred.max(1)[1]
    gold = gold.contiguous().view(-1)
    
    non_pad_mask = gold.ne(trg_pad_idx)
    n_correct = pred.eq(gold).masked_select(non_pad_mask).sum().item()
    n_word = non_pad_mask.sum().item()

    return loss, n_correct, n_word


def save_model(model, tokenizer, optimizer, step, model_path):
    try:

        Path(model_path).mkdir(parents=True, exist_ok=True)
        
        state = {
            'model_state_dict': model.state_dict(),
            'step': step,
        }
        torch.save(state, model_path + "/model_state.pt")
        tokenizer.save_pretrained(model_path)
        print(f" model saved -> {model_path}")

    except Exception as e:
        print(e)


def load_model(model, model_path):
    filename = model_path + "/model_state.pt"
    checkpoint = torch.load(filename)
    model.load_state_dict(checkpoint['model_state_dict'])
    step = checkpoint['step']    

    return model, step