# LexPerto

An LLM-powered application for generating court ruling drafts from input documents.

## Overview

LexPerto uses large language models to analyze legal documents and generate draft court rulings. This tool aims to assist legal professionals by automating the initial drafting process while maintaining accuracy and adhering to legal standards.

## Release Announcement

### LexPerto 0.1
Lexperto veröffentlicht die Version 0.1 seiner Software, mit der der Sachverhalt und die abstrakten Erwägungen automatisch
auf Basis der Beschwerde und Verfügung generiert werden. Die Software hat noch kein GUI, sondern man kann die notwendige Funktion in Python ausführen.
Das Ergebnis wird als Word-Dokument gespeichert.

### Lexperto 0.2

Lexperto veröffentlicht eine Integration in Microsoft Word, die es ermöglicht, die Generierung von Sachverhalt und abstrakten Erwägungen, direkt in Word zu generieren.
Man kann den entsprechenden Case-Folder spezifizieren und auf Generieren klicken. Danach kann man wie gewohnt im Word Dokument weiterarbeiten.

### Lexperto 0.3

Lexperto veröffentlich eine Version die automatisiert auf Basis von max. 5 Gerichtsurteilen, die Struktur des Dokument automatisch generiert.
Und aus Basis von Input-Dokumenten (Beschwerde, Verfügung) den Sachverhalt und die abstrakten Erwägungen generiert. Zuerst wird eine generisches Dokument generiert, welches der Nutzer
anpassen kann. Dieses wird dann in Word geöffnet, der Case-Folder ausgewählt und die spezifische Generierung gestartet.




## Features

- Process legal documents in various formats (PDF, DOCX, TXT)
- Generate structured court ruling drafts
- Customize output based on jurisdiction and case type
- Maintain references to source materials

