"""Train a java-based BERT model.

This script executes the pretraining of a BERT model.
A pretrained tokenizer is required which is used for a MLM training task.
"""
import argparse
import json

from tokenizers import Tokenizer
from tokenizers.pre_tokenizers import PreTokenizer
from transformers import BertConfig
from transformers import BertForMaskedLM
from transformers import DataCollatorForLanguageModeling
from transformers import PreTrainedTokenizerFast
from transformers import Trainer, TrainingArguments

from JavaPreTokenizer import JavaPreTokenizer


def main(tokenizer, output):
    tokenizer = Tokenizer.from_file(tokenizer)
    tokenizer.pre_tokenizer = PreTokenizer.custom(JavaPreTokenizer())
    tok = PreTrainedTokenizerFast(tokenizer_object=tokenizer)
    print(tok.unk_token)
    tok.add_special_tokens({
        'unk_token': '[UNK]',
        'mask_token': '[MASK]',
        'pad_token': '[PAD]',
        'cls_token': '[CLS]'
    })

    from datasets import load_dataset

    with open('train-split.json') as fp:
        train_files = json.load(fp)

    data = list(map(lambda x: '../' + x['filename'], train_files))

    ds = load_dataset('JavaDataset', split='train', data_files=data)
    ds_mapped = ds.map(lambda batch: tok(batch['code'], truncation=True, padding=True, max_length=512), batched=True)

    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tok, mlm=True, mlm_probability=0.15
    )

    config = BertConfig(
        vocab_size=8000,
        max_position_embeddings=514,
        num_attention_heads=12,
        num_hidden_layers=6,
        type_vocab_size=1,
    )

    model = BertForMaskedLM(config=config)

    training_args = TrainingArguments(
        output_dir=output,
        overwrite_output_dir=True,
        num_train_epochs=1,
        # per_gpu_train_batch_size=64,
        save_steps=10_000,
        save_total_limit=2,
        prediction_loss_only=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=data_collator,
        train_dataset=ds_mapped,
    )

    trainer.train()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Train a java-based BERT model.')
    parser.add_argument('tokenizer_file', type=str,
                        help='The file name to which the tokenizer will be stored.')
    parser.add_argument('bert_output', type=str, default='./Bert',
                        help='The file name to which the tokenizer will be stored.')
    args = parser.parse_args()
    main(vars(args)['tokenizer_file'], vars(args)['bert_output'])
