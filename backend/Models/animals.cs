using System.ComponentModel.DataAnnotations.Schema;
using System.ComponentModel.DataAnnotations;

namespace backend.Models
{
    public class animals
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int id { get; set; }
        public string name { get; set; }

        public int? animal_type_id { get; set; }
        [ForeignKey("animal_type_id")]
        public animal_types animal_type { get; set; }

        public int? habitat_id { get; set; }
        [ForeignKey("habitat_id")]
        public habitats habitat { get; set; }

        public string description { get; set; }
        public string? preview_id { get; set; }
        public string? video_id { get; set; }

        public int? test_id { get; set; }
        [ForeignKey("test_id")]
        public tests test { get; set; }

        // Списки
        public List<favorite_animals> favorite_animals { get; set; } = new();
    }
}
