
Tout d'abord, merci de considérer participer à notre projet !

ELSA est un projet open source et nous aimons recevoir des contributions de notre communauté ! Il y a plusieurs manières de contribuer; que ce soit en soumettant des bug reports, en contribuant du code directement ou simplement en nous disant comment vous utilisez ELSA.

L'*issue tracker* de Github n'est pas supposé être utilisé pour du support; n'hésitez pas à nous contacter directement à destin-informatique.com si vous en avez besoin.

Si vous n'avez jamais contribué, voici quelques liens utiles : http://makeapullrequest.com/ et https://www.firsttimersonly.com/.

Vous êtes fins prêt à faire des changements ! N'hésitez pas à demander l de'aide, on a tous été débutants à un moment !


## Comment signaler un bug

Merci d'intégrer un maximum d'informations afin de simplifier la vie de tout le monde et de résoudre les problèmes plus rapidement.

Exemples d'informations utiles : log d'ELSA, matériel (RPi 2 ou 3, éventuels boards et capteurs supplémentaires), comportement remarqué, comportement attendu, étapes pour reproduire le problème, etc


## Comment coder
Toutes les contributions sont bienvenues ! Nous utilisons git flow. La branche master est contient la dernière version stable du programme. Nous utilisons les branches 'features/xx' de git flow pour les grands changements; les petites modifications se font directement dans develop.

## Petit rappel pour git flow
https://danielkummer.github.io/git-flow-cheatsheet/
commencer une feature : `git flow feature start maFeature`

faire toute ses modifications et commits dans une branche

finir une feature et la merger dans develop : `git flow feature finish maFeature`

pour publier de develop vers master:

on crée une release en local : `git flow release start maRelease`

on la push afin qu'elle soit testée : `git flow release publish maRelease`

on la merge dans master : `git flow release finish maRelease`
