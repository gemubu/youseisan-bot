# Youseisan
ようせいさん discord_botとwebアプリ

## ブランチの構造
```
-main (リリースブランチ)
    |
    |-dev (開発ブランチ)
        |
        |-{username} (個人開発ブランチ)
        |-{username}
```

## 開発環境構築
リポジトリをクローン
```
$ git clone https://github.com/gemubu/Youseisan
```

仮想環境の構築(↓よくわかんなかったらvcいる時に聞いて)
```
$ cd Youseisan
Youseisan $ python3 -m venv venv
Youseisan $ source venv/bin/activate
```
この先開発はvenv環境で行う<br>
vscodeのターミナルにvenvの表示がなければvenv環境に入る
```
(venv)Youseisan $ source venv/bin/activate
```

依存関係のインストール
```
(venv)Youseisan $ pip install -r requirements.txt
```

個人ブランチの作成({username} には自分の名前を入力)
```
git checkout dev
git checkout -b username
```
