import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-{{component-name-kebab}}',
  standalone: true,
  imports: [CommonModule /* add required modules here */],
  templateUrl: './{{component-name-kebab}}.component.html',
  styleUrls: ['./{{component-name-kebab}}.component.scss']
})
export class {{ComponentNamePascal}}Component implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  // component inputs, outputs, and properties

  constructor(
    // inject services here
  ) {}

  ngOnInit(): void {
    // initialization
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // component methods
}
