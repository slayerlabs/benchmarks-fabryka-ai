#!/usr/bin/env bash
# Etapy na instancji vast.ai (2x RTX 4090). Odpalane z komputera lokalnego pojedynczym wywołaniem:
#   ssh -i <klucz> -p PORT root@sshN.vast.ai 'bash /workspace/kod/slayer-1b/testy_danych_slayer/na_instancji.sh ETAP ARG...'
# Etapy długie startują w tle (nohup) i kończą się plikiem /workspace/stan/<nazwa>.ok albo .blad.
# Kolejność i czasy: README.md w tym katalogu.
set -euo pipefail
K=/workspace/kod/slayer-1b
WS=/workspace
ST=$WS/stan
mkdir -p "$ST" "$WS/wyniki" "$WS/logi"
export PYTHONUNBUFFERED=1 HF_HUB_ENABLE_HF_TRANSFER=0

w_tle() {  # w_tle NAZWA KOMENDA...  -> log w logi/NAZWA.log, stan .ok/.blad
  local n=$1; shift
  rm -f "$ST/$n.ok" "$ST/$n.blad"
  nohup bash -c "( $* ) && touch $ST/$n.ok || touch $ST/$n.blad" > "$WS/logi/$n.log" 2>&1 &
  echo "start $n (pid $!), log $WS/logi/$n.log"
}

etap=${1:-}
case "$etap" in
  przygotuj)  # przygotuj LIMIT_S : bezpiecznik, zależności, wagi i checkpointy, łatka trenera
    LIMIT=${2:?limit sekund bezpiecznika}
    nohup python $K/wygaszanie/bezpiecznik.py po "$LIMIT" > $WS/logi/bezpiecznik.log 2>&1 &
    python $K/wygaszanie/bezpiecznik.py sprawdz
    pip install -q tokenizers datasets pyarrow huggingface_hub safetensors
    python $K/wygaszanie/pobierz.py $WS
    python $K/wygaszanie/konwertuj.py $WS/ckpt/ckpt_13848.pt $WS/m106 $WS/model_13848 --porownaj
    python $K/wygaszanie/konwertuj.py $WS/ckpt/ckpt_13800.pt $WS/m106 $WS/model_13800
    python $K/wygaszanie/latka_trenera.py $WS/m106/train_gpt_ref_r23.py $WS/train_wyg.py
    python $WS/train_wyg.py --help > $WS/trener_help.txt 2>&1 || true
    nproc; free -g; df -h $WS; nvidia-smi --query-gpu=name,memory.total --format=csv
    ;;
  dane)  # dane TOKENY_TRAIN : trzy ramiona + wspólny heldout (CPU, w tle)
    T=${2:-135e6}
    w_tle dane python $K/testy_danych_slayer/dane_ramion.py --tokenizer $WS/m106/tokenizer.json \
      --wyjscie $WS/dane_ramion --tokeny_train "$T" --cache $WS/hf_pliki --procesy "$(nproc)"
    ;;
  ewaluuj)  # ewaluuj ETYKIETA GPU ZAKRES(glowne|szuflada|heldout|wszystko) : model w $WS/model_ETYKIETA
    E=${2:?}; G=${3:?}; Z=${4:-wszystko}
    M=$WS/model_$E
    cmd=""
    if [[ $Z == heldout || $Z == wszystko ]]; then
      cmd+="CUDA_VISIBLE_DEVICES=$G python $K/testy_danych_slayer/heldout_bpb.py --model $M --dane $WS/dane_ramion/heldout --wyjscie $WS/wyniki/heldout_$E.json; "
    fi
    if [[ $Z == glowne || $Z == wszystko ]]; then
      cmd+="CUDA_VISIBLE_DEVICES=$G python $K/testy_danych_slayer/ewal_ramion.py --model $M --wyjscie $WS/wyniki/$E; "
    fi
    if [[ $Z == szuflada || $Z == wszystko ]]; then
      cmd+="CUDA_VISIBLE_DEVICES=$G python $K/testy_danych_slayer/ewal_ramion.py --model $M --szuflada --wyjscie $WS/szuflada/$E; "
    fi
    w_tle "ewal_${E}_${Z}" "$cmd"
    ;;
  trenuj)  # trenuj RAMIE GPU K : od ckpt_13848, LR liniowo 6e-4 -> 0 na K krokach, konwersja do $WS/model_RAMIE
    # Flagi jak ramie.sh przebiegu wygaszania (instancja 58351985): trener wznawia z <out-dir>/ckpt.pt
    # i po ostatnim kroku zawsze zapisuje <out-dir>/ckpt.pt (os.replace zastępuje dowiązanie plikiem).
    R=${2:?}; G=${3:?}; KR=${4:?}
    [[ -f $ST/dane.ok ]] || { echo "STOP: dane nie są gotowe ($ST/dane.ok)"; exit 2; }
    [[ -f $WS/dane_ramion/$R/train.bin ]] || { echo "STOP: brak danych ramienia $R"; exit 2; }
    D=$WS/runs/$R
    mkdir -p "$D"
    ln -sf $WS/ckpt/ckpt_13848.pt "$D/ckpt.pt"
    KONIEC=$((13848 + KR))
    w_tle "trening_$R" "CUDA_VISIBLE_DEVICES=$G WYGASZANIE_SCHED=liniowa WYGASZANIE_START=13848 \
      PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True python $WS/train_wyg.py \
      --data-dir $WS/dane_ramion/$R --out-dir $D --run-id $R --resume \
      --steps $KONIEC --batch 256 --grad-accum 128 --block 4096 --dtype uint16 --vocab 32768 \
      --n-layer 20 --n-embd 2048 --n-head 16 --norm rmsnorm --norm-eps 1e-6 --pos rope --rope-theta 500000 \
      --ffn swiglu --ffn-mult 2.667 --value-residual --qk-norm --attn-bias 0 --logit-cap 0 --z-loss 0 \
      --optimizer muon --lr 6e-4 --muon-lr 0.02 --wd 0.1 --grad-clip 1.0 \
      --data-seed 20261023 --sampler random --act-ckpt --loss-chunk 1024 --compile \
      --log-every 1 --eval-every 1000000 --ckpt-every 1000000 \
      && grep -q 'RESUME @ 13848' $WS/logi/trening_$R.log \
      && bash $K/testy_danych_slayer/na_instancji.sh konwertuj_koniec $R $KONIEC"
    ;;
  konwertuj_koniec)  # konwertuj_koniec RAMIE KROK : tylko końcowy ckpt.pt (plik, nie dowiązanie) o kroku == KROK
    R=${2:?}; KONIEC=${3:?}
    C=$WS/runs/$R/ckpt.pt
    [[ -f $C && ! -L $C ]] || { echo "STOP: $C nie istnieje albo jest dowiązaniem do ckpt startowego"; exit 3; }
    python $K/wygaszanie/konwertuj.py "$C" $WS/m106 $WS/model_$R
    python -c "import json,sys; s=json.load(open('$WS/model_$R/config.json'))['step']; print('krok', s); sys.exit(0 if s == $KONIEC else 4)"
    ;;
  stan)  # stan : pliki stanu, ostatnie linie logów, GPU
    ls -la $ST; for f in $WS/logi/*.log; do echo "== $f"; tail -n 3 "$f"; done
    nvidia-smi --query-gpu=index,utilization.gpu,memory.used --format=csv
    ;;
  pakuj)  # pakuj ETYKIETA : stan bieżący po rundzie; wyniki główne i szuflada w OSOBNYCH archiwach
    E=${2:?etykieta, np. po_bazach, po_rundzie1, koniec}
    tar -czf $WS/glowne_$E.tar.gz -C $WS wyniki logi stan $(cd $WS && ls -d dane_ramion/statystyki.json pobrane.json trener_help.txt 2>/dev/null)
    if [[ -d $WS/szuflada ]]; then tar -czf $WS/szuflada_$E.tar.gz -C $WS szuflada; fi
    ls -la $WS/*_$E.tar.gz
    ;;
  *)
    echo "etapy: przygotuj LIMIT_S | dane [TOKENY] | ewaluuj ETYKIETA GPU ZAKRES | trenuj RAMIE GPU K | konwertuj_koniec RAMIE KROK | stan | pakuj ETYKIETA"; exit 2
    ;;
esac
