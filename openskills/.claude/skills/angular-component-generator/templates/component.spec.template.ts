import { ComponentFixture, TestBed } from '@angular/core/testing';
import { {{ComponentNamePascal}}Component } from './{{component-name-kebab}}.component';

describe('{{ComponentNamePascal}}Component', () => {
  let component: {{ComponentNamePascal}}Component;
  let fixture: ComponentFixture<{{ComponentNamePascal}}Component>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [{{ComponentNamePascal}}Component]
    }).compileComponents();
    fixture = TestBed.createComponent({{ComponentNamePascal}}Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  // Additional tests here
});
