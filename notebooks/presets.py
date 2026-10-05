"""Named dataset presets, so switching dataset on the night is one word."""

PRESETS = {
    "transactions": {
        "path": "../data/laramee2026/laramee26openBankTransactionData.csv.gz",
        "fields": ["Transaction Description"],
        "label_field": "Category",
        "filter": ("Transaction Type", {"DEB", "DD"})
    },
    "senedd": {
        "path": "../data/senedd/senedd.csv.gz",
        "fields": ["text"],
        "label_field": "committee",
        "filter": None
    },
    "git_linux": {
        "path": "../data/git_log/git_log.csv.gz",
        "fields": ["message"],
        "label_field": "scope",
        "filter": ("scope", {"drm", "xfs", "bpf", "kvm", "bluetooth", "iio"})
    },
    "git_pytorch": {
        "path": "../data/git_log/git_log.csv.gz",
        "fields": ["message"],
        "label_field": "scope",
        "filter": ("scope", {"dynamo", "inductor", "mps", "rocm", "distributed"})
    },
}
