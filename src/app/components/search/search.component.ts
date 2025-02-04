import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { SearchService } from '../../services/search.service';
import { 
  IonList, 
  IonItem, 
  IonLabel, 
  IonCheckbox, 
  IonButton, 
  IonInput,
  IonCard,
  IonCardContent
} from '@ionic/angular/standalone';

@Component({
  selector: 'app-search',
  templateUrl: './search.component.html',
  styleUrls: ['./search.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    IonList,
    IonItem,
    IonLabel,
    IonCheckbox,
    IonButton,
    IonInput,
    IonCard,
    IonCardContent
  ]
})
export class SearchComponent {
  searchForm: FormGroup;
  archives = [
    { id: '0', name: 'Desuarchive' },
    { id: '1', name: 'Palanq' },
    { id: '2', name: 'Moe' },
    { id: '3', name: '4plebs' },
    { id: '4', name: 'b4k' }
  ];

  constructor(
    private fb: FormBuilder,
    private searchService: SearchService
  ) {
    this.searchForm = this.fb.group({
      query: ['', Validators.required],
      archives: this.fb.array(this.archives.map(() => false))
    });
  }

  onSubmit() {
    if (this.searchForm.valid) {
      const selectedArchives = this.searchForm.value.archives
        .map((checked: boolean, i: number) => checked ? this.archives[i].id : null)
        .filter((id: string | null) => id !== null);

      if (selectedArchives.length === 0) {
        alert('Please select at least one archive.');
        return;
      }

      this.searchService.search(this.searchForm.value.query, selectedArchives)
        .subscribe(results => {
          this.searchService.updateResults(results);
        });
    }
  }
} 